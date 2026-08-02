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

    # 3. Call the Compliance Tool (RAG retrieval + audit generation)
    #
    # FIX (weak point #9): the old version took this already-generated audit
    # report (check_labor_compliance -> empower_search already runs its own
    # GPT-4o call that produces a full compliance audit against the RAG
    # context) and fed it into a *second*, near-duplicate LLM call here,
    # asking gpt-4o-mini to re-analyze the same thing again. That's two
    # sequential model calls doing overlapping work on every single legal
    # query -- extra cost and latency for no measurable quality gain, since
    # the second call had no new information the first call didn't already
    # have (it doesn't even have `user_skills`/location, only free text).
    #
    # search.py's empower_search is the *only* place that does the actual
    # law-context-grounded reasoning now; this node's job is purely to
    # build the right query (with real location + skills) and pass the
    # result along as the specialist report -- no redundant re-analysis.
    audit_result = check_labor_compliance.invoke({"query": search_query})

    # 5. Return the report to the state
    return {
        "messages": [AIMessage(content=f"LEGAL_AUDIT_REPORT:\n{audit_result}")],
        "next_agent": "supervisor",
        "specialist_done": True,
    }
