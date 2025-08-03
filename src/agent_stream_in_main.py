import sys
import os
import asyncio
from config import BasicConfig
from create_or_update_vectorstore import KnowledgeManager
from langgraph.graph import StateGraph, START, add_messages
from typing_extensions import TypedDict, Annotated, List, Literal
from pydantic import BaseModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig

user_config = BasicConfig()
knowledge_manager = KnowledgeManager()
checkpointer = InMemorySaver()


class AgentGraph(TypedDict):
    """Agent graph configuration"""
    messages: Annotated[List[BaseMessage], add_messages]
    sources: Annotated[str, "Sources of the retrieved documents"]
    retrieved_docs: Annotated[List[BaseMessage], "Retrieved documents"]
    # stream_chunk: Annotated[List[str], "Streamed response chunks"]

class router_state(BaseModel):
    "State of router node"
    intent: Literal['query', 'general']

async def query_node(state: AgentGraph):
    "Query node to search knowledge base"
    messages = state['messages']
    latest_message = messages[-1].content if messages else ""
    if not str(latest_message).strip():
        print("[DEBUG] Latest message is empty or invalid.")
        return {
            "messages": [AIMessage(content="Your query is empty. Please provide a valid question.")],
            "sources": "",
            "retrieved_docs": []
        }

    retriever = knowledge_manager.knowledge_base.as_retriever(search_kwargs={"k": 5})
    docs = await retriever.ainvoke(str(latest_message))
    if not docs:
        print("[DEBUG] No documents retrieved from the knowledge base.")
        return {
            "messages": [AIMessage(content="No relevant information found in the knowledge base.")],
            "sources": "",
            "retrieved_docs": []
        }

    context = "\n".join([doc.page_content for doc in docs if doc.page_content.strip()])
    if not context:
        context = "No relevant information found in the knowledge base."
        print("[DEBUG] Using default context as no valid content was retrieved.")

    sources = "\n".join([doc.metadata.get("source", "") for doc in docs])

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""Please answer the question based on the context provided below.
                    Context: {context}"""),
        MessagesPlaceholder(variable_name="history"),
    ])

    chain = prompt | user_config.MODEL
    chain.with_config(run_name="query_chain")

    response = await chain.ainvoke({"history": messages})
    return {
        "messages": [AIMessage(content=str(response))],
        "sources": sources,
        "retrieved_docs": docs
    }

async def router_function(state: AgentGraph):
    """Router function to determine the next node based on intent"""
    messages = state['messages']
    latest_message = messages[-1].content if messages else ""
    model_with_structed = user_config.MODEL.with_structured_output(router_state)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that determines the user's intent."),
        ("human", f"""The user said: "{latest_message}". 
                    Determine if the intent is to 'query' the knowledge base or to have a 'general' conversation. 
                    Respond with either 'query' or 'general'."""),
        MessagesPlaceholder(variable_name="history")
    ])

    chain = prompt | model_with_structed
    result = await chain.ainvoke({"history": messages})
    print(f"[DEBUG] Router intent result: {result}") 
    if not isinstance(result, router_state):
        return "general"

    return result.intent

async def process_general(state: AgentGraph):
    """process intent general"""
    response = "Cthulhu disturbs your mind, but you are not ready to face it yet.\n"
    print(response, flush=True)
    return {
        "messages": [AIMessage(content=response)]
    }

async def get_graph():
    """Create the agent graph with nodes and edges"""
    workflow = StateGraph(AgentGraph)
    workflow.add_node("query", query_node)
    workflow.add_node("process_general", process_general)

    workflow.add_conditional_edges(
        source=START,
        path=router_function,
        path_map={
            "query": "query",
            "general": "process_general"
        }
    )

    workflow = workflow.compile(checkpointer=checkpointer)
    return workflow
    
async def main():
    """Main function to run the agent graph"""
    workflow = await get_graph()
    config :RunnableConfig = {"configurable": {"thread_id": "1"}}

    print("Starting...(use 'exit' or 'quit' to stop, maybe you should not whisper too much...)")
    while True:
        user_input = input("\nYou: Whisper something:").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Exiting...")
            break
        if not user_input:
            print("Louder, someone can't hear you!")
            continue

        try:
            user_message = HumanMessage(content=user_input)
            async for event in workflow.astream_events({
                "messages": [user_message],
                "sources": "",
                "retrieved_docs": []
            }, config=config, stream_mode="updates"):
                # print(event)
                # print("\n")
                if event["event"] == 'on_chat_model_stream' and event["data"]["chunk"].content is not None:
                    print(event["data"]["chunk"].content, end='', flush=True)
        except Exception as e:
            print(f"HA, bad message: {e}")
            print("Try again, but don't lose your mind...\n")

if __name__ == "__main__":
    asyncio.run(main())



