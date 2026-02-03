import logging
from langchain_openai import ChatOpenAI
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
    user_skills = state.get("user_skills", "General Worker")
    location = state.get("location_name", "West Bengal")
    
    logger.info(f"⚖️ Legal Node: Initiating audit for {user_skills} in {location}")

    # 2. Formulate the RAG Query
    # We combine user skills and location to get the exact minimum wage entry
    search_query = f"2026 minimum wage and labor rights for {user_skills} in {location}, West Bengal"
    
    # 3. Call the Compliance Tool (The RAG Retrieval)
    legal_data = check_labor_compliance.invoke({"query": search_query})

    # 4. Analysis Logic
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    analysis_prompt = f"""
    You are the Legal Auditor for EmpowerNet. 
    Analyze the user's message against the provided 2026 Labor Laws.

    LABOR LAW CONTEXT (RAG):
    {legal_data}

    USER MESSAGE:
    "{last_user_msg}"

    YOUR TASK:
    1. Identify if the user's reported wage is BELOW the legal minimum for a {user_skills}.
    2. Check if any other rights (overtime, breaks, safety gear) are being violated.
    3. Summarize the findings technically. 
    
    NOTE: Do not talk to the user directly. Just provide the audit report for the next node.
    """
    
    audit_result = llm.invoke(analysis_prompt).content

    # 5. Return the report to the state
    return {
        "messages": [AIMessage(content=f"LEGAL_AUDIT_REPORT:\n{audit_result}")],
        "next_agent": "supervisor"
    }