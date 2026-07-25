import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage

from app.graph.state import AgentState
from app.graph.nodes import AgenticNodes

logger = logging.getLogger(__name__)

# Instantiate nodes
nodes = AgenticNodes()

# --- Conditional Routing Functions ---

def route_after_retrieve(state: Dict[str, Any]) -> Literal["retrieve", "generate_rag"]:
    """
    Decides whether to retrieve again or proceed to generation.
    We retrieve strictly once to minimize response latency.
    """
    logger.info("Routing to generate (one-pass search optimization).")
    return "generate_rag"

def route_after_generate(state: Dict[str, Any]) -> Literal["tool_node", "grade_generation", "end"]:
    """
    Checks if the generated response contains tool calls or is a conversational/tool query
    to route to the correct node or end immediately.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(f"LLM requested tool calls: {[tc['name'] for tc in last_message.tool_calls]}. Routing to Tool Node.")
        return "tool_node"
    
    # Check if there are any tool calls or tool responses in history
    from langchain_core.messages import ToolMessage, AIMessage
    has_tool_in_history = any(
        isinstance(msg, ToolMessage) or 
        (isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls)
        for msg in messages
    )
    if has_tool_in_history:
        logger.info("LLM generated response after tool execution. Skipping hallucination grader. Routing to END.")
        return "end"
        
    # Skip hallucination grading if retrieval documents were irrelevant (conversational query)
    if state.get("web_search_needed", False):
        logger.info("Context is irrelevant (conversational input). Skipping hallucination grader. Routing to END.")
        return "end"
    
    logger.info("LLM generated text response. Routing to Hallucination Grader.")
    return "grade_generation"

def route_after_grade_generation(state: Dict[str, Any]) -> Literal["generate_rag", "end"]:
    """
    Evaluates the hallucination grade. If hallucinations are found, routes back to generate again.
    """
    hallucination_detected = state.get("web_search_needed", False)
    
    # We can track generation retries in the messages or metadata
    # For safety, let's limit regeneration to 1 retry
    messages = state["messages"]
    system_messages_count = sum(1 for m in messages if getattr(m, "content", "").startswith("System: Hallucination detected"))
    
    if hallucination_detected and system_messages_count < 2:
        logger.warning("Hallucination detected! Routing back to generate for correction.")
        # Inject warning message into state for LLM awareness
        state["messages"].append(SystemMessage(content="System: Hallucination detected. Your previous response was not fully grounded in the retrieved documents. Please regenerate the response using strictly the provided facts."))
        return "generate_rag"
    
    logger.info("Response graded as grounded and correct. Routing to END.")
    return "end"


# --- Assemble State Graph ---

workflow = StateGraph(AgentState)

# 1. Register Nodes
workflow.add_node("retrieve", nodes.retrieve_node)
workflow.add_node("grade_documents", nodes.grade_documents_node)
workflow.add_node("rewrite_query", nodes.rewrite_query_node)
workflow.add_node("generate_rag", nodes.generate_rag_node)
workflow.add_node("grade_generation", nodes.grade_generation_node)
workflow.add_node("tool_node", nodes.tool_node)

# 2. Setup Edges
workflow.set_entry_point("retrieve")

# From retrieve, we transition to grading documents
workflow.add_edge("retrieve", "grade_documents")

# From grading documents, we conditionally route to rewrite_query (which goes back to retrieve) or generate_rag
workflow.add_conditional_edges(
    "grade_documents",
    route_after_retrieve,
    {
        "retrieve": "rewrite_query",
        "generate_rag": "generate_rag"
    }
)

# From rewrite_query, we loop back to retrieve
workflow.add_edge("rewrite_query", "retrieve")

# From generate_rag, we conditionally route to tool_node or grade_generation
workflow.add_conditional_edges(
    "generate_rag",
    route_after_generate,
    {
        "tool_node": "tool_node",
        "grade_generation": "grade_generation",
        "end": END
    }
)

# From tool_node, we return to generate_rag to process tool execution results
workflow.add_edge("tool_node", "generate_rag")

# From grade_generation, we conditionally route to generate_rag (for retry) or END
workflow.add_conditional_edges(
    "grade_generation",
    route_after_grade_generation,
    {
        "generate_rag": "generate_rag",
        "end": END
    }
)

from langgraph.checkpoint.memory import MemorySaver

# 3. Compile Workflow with checkpointer
compiled_graph = workflow.compile(checkpointer=MemorySaver())
