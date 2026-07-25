import logging
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

from app.api.dependencies import get_current_user_context
from app.core.security import UserContext, TokenManager
from app.graph.workflow import compiled_graph

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api", tags=["Chat"])

@router.get("/auth/tokens")
async def get_portal_tokens():
    """
    Returns pre-signed developer JWT tokens for all 4 enterprise client portals.
    """
    return {
        "hr": TokenManager.generate_token(scope="hr", role="employee", user_id="emp_hr_001"),
        "it": TokenManager.generate_token(scope="it", role="employee", user_id="emp_it_002"),
        "support": TokenManager.generate_token(scope="customer_support", role="agent", user_id="agent_supp_003"),
        "sales": TokenManager.generate_token(scope="sales", role="sales_rep", user_id="rep_sales_004")
    }

class ChatPayload(BaseModel):
    message: str = Field(..., description="The query/prompt message to send to the RAG Agent")
    thread_id: str = Field("default-session", description="The thread identifier to persist chat history")

class ChatResponse(BaseModel):
    response: str
    scope: str
    role: str
    references: list

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatPayload, 
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Unified chat endpoint serving all 4 chatbot interfaces.
    Verifies JWT token, injects the scope & role context, and executes the compiled LangGraph workflow.
    """
    logger.info(f"Incoming chat request for scope={user_context.scope}, role={user_context.role}, thread={payload.thread_id}")
    
    # Initialize the AgentState input dictionary
    initial_state = {
        "messages": [HumanMessage(content=payload.message)],
        "scope": user_context.scope,
        "role": user_context.role,
        "retrieved_docs": [],
        "generation": ""
    }
    
    # Pass thread_id to config for the MemorySaver checkpointer
    config = {"configurable": {"thread_id": payload.thread_id}}
    
    try:
        # Run the self-correcting agent workflow asynchronously with checkpointer
        result = await compiled_graph.ainvoke(initial_state, config)
        
        # Extract response text
        generation = result.get("generation", "I'm sorry, I encountered an issue generating an answer.")
        
        # Format references for the frontend
        references = []
        for doc in result.get("retrieved_docs", []):
            references.append({
                "source": doc["metadata"].get("source_file", "Unknown"),
                "page": doc["metadata"].get("page_number", 1),
                "rrf_score": round(doc.get("rrf_score", 0.0), 4)
            })
            
        return ChatResponse(
            response=generation,
            scope=user_context.scope,
            role=user_context.role,
            references=references
        )
    except Exception as e:
        logger.error(f"Error running LangGraph agent workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agentic engine error: {str(e)}"
        )

@router.post("/chat/stream")
async def chat_stream_endpoint(
    payload: ChatPayload, 
    user_context: UserContext = Depends(get_current_user_context)
):
    """
    Unified streaming chat endpoint. Returns Server-Sent Events (SSE) token chunks in real-time.
    """
    logger.info(f"Incoming streaming request for scope={user_context.scope}, role={user_context.role}, thread={payload.thread_id}")
    
    async def event_generator():
        config = {"configurable": {"thread_id": payload.thread_id}}
        initial_state = {
            "messages": [HumanMessage(content=payload.message)],
            "scope": user_context.scope,
            "role": user_context.role,
            "retrieved_docs": [],
            "generation": ""
        }
        
        try:
            # Stream tokens natively from nodes using stream_mode="messages"
            async for chunk, metadata in compiled_graph.astream(initial_state, config, stream_mode="messages"):
                node_name = metadata.get("langgraph_node")
                
                # Yield token chunks from the ChatGroq model inside generate_rag node
                if node_name == "generate_rag" and chunk.content:
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"
            
            # Fetch final state from memory checkpointer to extract retrieved documents
            final_state = await compiled_graph.aget_state(config)
            retrieved_docs = final_state.values.get("retrieved_docs", []) if final_state else []
            if retrieved_docs:
                refs = [
                    {
                        "source": doc["metadata"].get("source_file", "Unknown"),
                        "page": doc["metadata"].get("page_number", 1),
                        "rrf_score": round(doc.get("rrf_score", 0.0), 4)
                    }
                    for doc in retrieved_docs
                ]
                yield f"data: {json.dumps({'references': refs})}\n\n"
                        
        except Exception as e:
            logger.error(f"Error in SSE stream generator: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': f'Agent error: {str(e)}'})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
