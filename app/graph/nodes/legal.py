# app/graph/nodes/legal.py

import logging
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.tools.compliance import check_labor_compliance

logger = logging.getLogger(__name__)

def legal_node(state: AgentState):
    """
    The Legal Specialist: Uses RAG results to audit wages and job compliance.
    """
    # 1. Gather context from the shared state
    messages = state.get("messages", [])
    last_user_msg = messages[-1].content if messages else ""
    user_skills = state.get("user_skills") or "General Worker"

    district = state.get("district")
    block = state.get("block")
    location_parts = [p for p in [block, district] if p]
    location = ", ".join(location_parts) if location_parts else "West Bengal"

    logger.info(f"⚖️ Legal Node: Initiating audit for {user_skills} in {location}")

    # 2. Formulate the RAG Query
    # We combine user skills and location to get the exact minimum wage entry
    search_query = f"2026 minimum wage and labor rights for {user_skills} in {location}, West Bengal"

    
    audit_result = check_labor_compliance.invoke({"query": search_query})

    # 5. Return the report to the state
    return {
        "messages": [AIMessage(content=f"LEGAL_AUDIT_REPORT:\n{audit_result}")],
        "next_agent": "supervisor",
        "specialist_done": True,
    }
