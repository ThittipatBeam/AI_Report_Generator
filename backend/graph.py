from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from backend.agents import run_data_retriever_agent, run_report_generator_agent

class AgentState(TypedDict):
    """
    State object passed between nodes in the LangGraph workflow.
    """
    query: str
    retrieved_snippets: Optional[str]
    final_report: Optional[str]

def data_retriever_node(state: AgentState) -> dict:
    """
    Node 1: Executes Agent 1 (Data Retriever Agent) to search knowledge_base.txt.
    """
    user_query = state["query"]
    snippets = run_data_retriever_agent(user_query)
    return {"retrieved_snippets": snippets}

def report_generator_node(state: AgentState) -> dict:
    """
    Node 2: Executes Agent 2 (Report Generator Agent) to synthesize retrieved snippets into a report.
    """
    user_query = state["query"]
    snippets = state.get("retrieved_snippets", "")
    report = run_report_generator_agent(user_query, snippets)
    return {"final_report": report}

# Build LangGraph StateGraph
workflow = StateGraph(AgentState)

# Add Agent Nodes
workflow.add_node("data_retriever", data_retriever_node)
workflow.add_node("report_generator", report_generator_node)

# Connect Nodes in a Sequential Agent Handoff Flow
workflow.set_entry_point("data_retriever")
workflow.add_edge("data_retriever", "report_generator")
workflow.add_edge("report_generator", END)

# Compile LangGraph app
agent_pipeline_graph = workflow.compile()

def run_agentic_rag_pipeline(user_query: str) -> str:
    """
    Executes the full LangGraph 2-Agent pipeline for a given user query.
    Returns the final synthesized report string.
    """
    initial_state = {
        "query": user_query,
        "retrieved_snippets": "",
        "final_report": ""
    }
    
    final_state = agent_pipeline_graph.invoke(initial_state)
    return final_state.get("final_report", "Error generating report.")
