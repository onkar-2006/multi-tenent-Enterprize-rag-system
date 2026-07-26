import logging
import json
from typing import List, Dict, Any, Literal
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.embeddings import OpenRouterEmbeddingClient
from app.db.pgvector_client import SupabaseVectorClient
from app.db.hybrid_retriever import ScopedHybridRetrieverManager
from app.graph.tools import get_authorized_tools

logger = logging.getLogger(__name__)

# --- Pydantic Schemas for Structured LLM Outputs ---
class GradeDocuments(BaseModel):
    binary_score: str = Field(
        description="Documents are relevant to the query, 'yes' or 'no'"
    )

class GradeHallucination(BaseModel):
    binary_score: str = Field(
        description="Answer is grounded in / supported by the retrieved documents, 'yes' or 'no'"
    )

class QueryIntent(BaseModel):
    intent: Literal["conversational", "domain_query"] = Field(
        description="Classify input: 'conversational' for greetings/small-talk/pleasantries/introductions, or 'domain_query' for specific policies/technical questions/actions."
    )


class AgenticNodes:
    """
    Enterprise-grade node handler class for the LangGraph Agentic RAG state machine.
    """
    def __init__(self):
        self.db_client = SupabaseVectorClient()
        self.embedding_client = OpenRouterEmbeddingClient()
        self.retriever_manager = ScopedHybridRetrieverManager(self.db_client, self.embedding_client)
        
        # Primary Groq model with automatic fallback models to prevent 429 rate limit errors
        primary_llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            temperature=0.0,
            max_retries=2
        )
        fallback_llm_1 = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama-3.1-8b-instant",
            temperature=0.0
        )
        fallback_llm_2 = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama3-8b-8192",
            temperature=0.0
        )
        self.llm = primary_llm.with_fallbacks([fallback_llm_1, fallback_llm_2])

    async def classify_intent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Zero-Shot LLM Intent Classifier Node.
        Categorizes query into 'conversational' or 'domain_query' in < 150ms.
        """
        logger.info("=== Executing Intent Classifier Node ===")
        query = state["messages"][-1].content
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an ultra-fast production query intent classifier for an enterprise RAG system.\n"
                       "Classify the user input into one of two categories:\n"
                       "1. 'conversational': Greetings, small talk, pleasantries, or general questions like 'who are you', 'hi', 'hello'.\n"
                       "2. 'domain_query': Specific questions about company policies, technical issues, IT, pricing, benefits, or actions.\n"
                       "Respond with JSON containing an 'intent' key set to 'conversational' or 'domain_query'."),
            ("human", "{query}")
        ])
        
        try:
            structured_llm = self.llm.with_structured_output(QueryIntent)
            chain = prompt | structured_llm
            res: QueryIntent = await chain.ainvoke({"query": query})
            intent = res.intent
        except Exception as e:
            logger.warning(f"Intent classification error ({e}), defaulting to domain_query.")
            intent = "domain_query"
            
        logger.info(f"Intent classified as '{intent}' for query: '{query}'")
        return {"intent": intent}

    @staticmethod
    def is_greeting_query(query: str) -> bool:
        """
        Fast intent classification check for simple conversational greetings.
        """
        clean = query.strip().lower().strip("!.?,")
        greetings = {
            "hi", "hii", "hiii", "hello", "hey", "heyy", "heyyy",
            "good morning", "good afternoon", "good evening",
            "who are you", "what can you do", "help", "help me"
        }
        return clean in greetings or (len(clean.split()) <= 2 and clean in greetings)

    async def retrieve_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieves relevant documents using the Scoped Hybrid Ensemble Retriever.
        """
        logger.info("=== Executing Retrieve Node ===")
        # Use the last message content as query
        query = state["messages"][-1].content
        scope = state["scope"]
        role = state["role"]

        # Instant Intent Bypass for Greetings (< 50ms response)
        if self.is_greeting_query(query):
            logger.info(f"Query '{query}' identified as conversational greeting. Bypassing hybrid vector search for instant response.")
            return {"retrieved_docs": [], "web_search_needed": True}

        # Perform hybrid RRF retrieval
        retrieved_docs = await self.retriever_manager.retrieve(query, scope, role, top_n=5)

        return {"retrieved_docs": retrieved_docs}

    async def grade_documents_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates the relevance of the retrieved documents to the query.
        Determines whether to proceed to generation or rewrite the query for a better search match.
        """
        logger.info("=== Executing Document Grading Node (Self-Reflection) ===")
        query = state["messages"][-1].content
        docs = state["retrieved_docs"]
        
        if not docs:
            logger.warning("No documents retrieved. Flagging search for rewrite.")
            return {"web_search_needed": True} # Re-use flag name or direct routing logic

        # Grade documents
        grader_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert evaluator grading the relevance of retrieved documents to a user query.\n"
                       "If the documents contain any information or keywords relevant to answering the query, "
                       "grade them as relevant. Respond with a JSON object containing a 'binary_score' of either 'yes' or 'no'."),
            ("human", "User query: {query}\n\nRetrieved Documents:\n{docs}")
        ])
        
        try:
            structured_grader = self.llm.with_structured_output(GradeDocuments)
            chain = grader_prompt | structured_grader
            formatted_docs = "\n\n".join([f"Doc {i+1}:\n{doc['content']}" for i, doc in enumerate(docs)])
            grade = await chain.ainvoke({"query": query, "docs": formatted_docs})
            
            score = grade.binary_score.lower().strip()
            logger.info(f"Document relevance grade: {score}")
            
            if score == "yes":
                return {"web_search_needed": False} # We use web_search_needed as a routing flag for "documents_relevant"
            else:
                return {"web_search_needed": True}
        except Exception as e:
            logger.error(f"Error during document grading: {e}. Defaulting to yes.")
            return {"web_search_needed": False}

    async def rewrite_query_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rewrites the query to optimize vector/keyword search matching.
        """
        logger.info("=== Executing Query Rewriting Node ===")
        messages = state["messages"]
        original_query = messages[-1].content
        
        rewriter_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI query rewriter. Your task is to analyze the user's question and "
                       "rewrite it to optimize search retrieval for a vector database and BM25 text index.\n"
                       "Output ONLY the raw rewritten search query, with no labels, explanation, or quotes."),
            ("human", "Rewrite this query: {query}")
        ])
        
        chain = rewriter_prompt | self.llm
        rewritten_msg = await chain.ainvoke({"query": original_query})
        rewritten_query = rewritten_msg.content.strip()
        logger.info(f"Original Query: '{original_query}' -> Rewritten: '{rewritten_query}'")
        
        # Append rewritten query as a system message/history for the next retrieval
        return {
            "messages": [HumanMessage(content=rewritten_query)],
            "loop_count": state.get("loop_count", 0) + 1
        }

    async def generate_rag_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates final answer using retrieved context, with prompt guardrails and dynamic tools.
        """
        logger.info("=== Executing Generate Node ===")
        messages = state["messages"]
        # Find the original user question (the first human message or last user query)
        user_query = messages[0].content if messages else ""
        docs = state["retrieved_docs"]
        scope = state["scope"]
        role = state["role"]
        
        # Formulate context text
        context_str = "\n\n".join([
            f"--- Source: {doc['metadata'].get('source_file', 'Unknown')} (Page {doc['metadata'].get('page_number', 1)}) ---\n{doc['content']}"
            for doc in docs
        ])
        
        system_prompt = (
            f"You are the central brain AI assistant for Tenant Domain/Scope: '{scope.upper()}', serving a user with Role: '{role.upper()}'.\n"
            f"Your mission is to assist the user by answering their inquiries clearly, helpfully, and concisely.\n\n"
            f"--- SECURITY BOUNDARY AND GUARDRAILS ---\n"
            f"1. Under no circumstances should you leak, make up, or reference policies outside your active scope: '{scope.upper()}'.\n"
            f"2. Be concise, direct, and helpful. Avoid unnecessary repetitive filler text or excessive multi-paragraph intro/outro statements.\n"
            f"3. For domain policy or technical questions, base your answers on the retrieved context snippets or authorized tools. If specific details are absent, politely state that current {scope.upper()} documentation does not cover that specific detail.\n\n"
            f"--- RETRIEVED CONTEXT SNIPPETS ---\n"
            f"{context_str if context_str else 'No document snippets retrieved for this conversational input.'}"
        )
        
        # Build prompt messages
        prompt_messages = [SystemMessage(content=system_prompt)]
        
        # Append conversation history
        for msg in messages:
            if isinstance(msg, (HumanMessage, AIMessage, SystemMessage, ToolMessage)):
                prompt_messages.append(msg)
                
        # Bind authorized tools dynamically based on scope/role
        authorized_tools = get_authorized_tools(scope, role)
        
        if authorized_tools:
            # Bind tools to the LLM
            llm_with_tools = self.llm.bind_tools(authorized_tools)
            chunks = []
            async for chunk in llm_with_tools.astream(prompt_messages):
                chunks.append(chunk)
            response = sum(chunks[1:], start=chunks[0]) if chunks else AIMessage(content="")
        else:
            chunks = []
            async for chunk in self.llm.astream(prompt_messages):
                chunks.append(chunk)
            response = sum(chunks[1:], start=chunks[0]) if chunks else AIMessage(content="")
            
        return {"generation": response.content, "messages": [response]}

    async def grade_generation_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grades the generation to ensure it contains no hallucinations and is fully supported by context.
        """
        logger.info("=== Executing Hallucination Grading Node (Self-Correction) ===")
        docs = state["retrieved_docs"]
        generation = state["generation"]
        
        if not docs:
            # No context means we can't verify grounding, assume passed
            return {"web_search_needed": False}
            
        grader_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an auditor checking for hallucinations in an AI generated answer.\n"
                       "Determine if the answer is completely grounded in and supported by the facts "
                       "listed in the retrieved context snippets. Respond with a JSON object containing "
                       "a 'binary_score' of either 'yes' (fully grounded, no hallucinations) or 'no' (contains hallucinations or unsupported facts)."),
            ("human", "Retrieved Context Snippets:\n{docs}\n\nGenerated Answer:\n{generation}")
        ])
        
        try:
            structured_grader = self.llm.with_structured_output(GradeHallucination)
            chain = grader_prompt | structured_grader
            formatted_docs = "\n\n".join([doc["content"] for doc in docs])
            grade = await chain.ainvoke({"docs": formatted_docs, "generation": generation})
            
            score = grade.binary_score.lower().strip()
            logger.info(f"Hallucination grading result: {score}")
            
            # Using web_search_needed as a flag for "hallucination detected" (True means hallucination detected, re-generate)
            if score == "yes":
                return {"web_search_needed": False} # Correct grounding, no hallucination
            else:
                return {"web_search_needed": True} # Hallucination detected, need to regenerate
        except Exception as e:
            logger.error(f"Error during hallucination grading: {e}. Defaulting to yes.")
            return {"web_search_needed": False}

    async def tool_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronously executes requested tool calls and returns results to state.
        """
        logger.info("=== Executing Tool Node ===")
        messages = state["messages"]
        last_message = messages[-1]
        
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            logger.warning("Tool node triggered but no tool calls found.")
            return {}
            
        # Get authorized tools for this caller
        authorized_tools = get_authorized_tools(state["scope"], state["role"])
        tools_map = {t.name: t for t in authorized_tools}
        
        tool_responses = []
        for tool_call in last_message.tool_calls:
            name = tool_call["name"]
            args = tool_call["args"]
            call_id = tool_call["id"]
            
            if name in tools_map:
                logger.info(f"Invoking tool '{name}' with args {args}")
                tool_obj = tools_map[name]
                try:
                    # Invoke tool synchronously
                    result = tool_obj.invoke(args)
                    tool_responses.append(ToolMessage(
                        content=str(result),
                        name=name,
                        tool_call_id=call_id
                    ))
                except Exception as e:
                    logger.error(f"Error executing tool {name}: {e}")
                    tool_responses.append(ToolMessage(
                        content=f"Error executing tool: {e}",
                        name=name,
                        tool_call_id=call_id
                    ))
            else:
                logger.warning(f"Attempted tool call for unauthorized/non-existent tool: {name}")
                tool_responses.append(ToolMessage(
                    content=f"Error: Tool '{name}' is not authorized or does not exist for your current scope/role.",
                    name=name,
                    tool_call_id=call_id
                ))
                
        return {"messages": tool_responses}
