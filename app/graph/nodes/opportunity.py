import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState

# Importing our three separate tool files
from app.tools.jobs import match_local_jobs
from app.tools.training import get_training_programs
from app.tools.community import find_nearby_shgs

logger = logging.getLogger(__name__)

def opportunity_node(state: AgentState):
    """
    The Opportunity Specialist: Triage and Match.
    Decides whether to look for Jobs, Training, or SHGs based on intent.
    """
    # 1. State Recovery & Guarding
    last_msg = state["messages"][-1].content if state.get("messages") else ""
    lat = state.get("lat")
    lon = state.get("lon")
    
    # CRITICAL FIX: Ensure skills is never None to prevent Pydantic errors
    skills = state.get("user_skills")
    if not skills or skills.lower() == "none":
        skills = "labor" 
    
    logger.info(f"🔍 Opportunity Node: Analyzing intent for skills '{skills}' at ({lat}, {lon})")

    # 2. Coordinate Check
    # If we have no location, we can't run spatial queries
    if lat is None or lon is None or (lat == 0.0 and lon == 0.0):
        return {
            "messages": [AIMessage(content="OPPORTUNITY_REPORT: Error - No location data available. Please ask the user for their village or to share a GPS pin.")],
            "next_agent": "supervisor"
        }

    # 3. Intent Analysis
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    intent_prompt = f"""
    Analyze the user's request: "{last_msg}"
    
    Identify the primary need:
    - 'JOB': User wants to find work or earn money.
    - 'TRAINING': User wants to learn, get a certificate, or join a government scheme.
    - 'SHG': User wants to join a group, save money, or get a loan.
    - 'ALL': If the user is just asking "What is available near me?" or a general greeting.
    
    Return ONLY the word: JOB, TRAINING, SHG, or ALL.
    """
    intent = llm.invoke(intent_prompt).content.strip().upper()
    logger.info(f"🎯 Intent Detected: {intent}")

    # 4. Selective Tool Execution
    results_summary = []

    if intent in ["JOB", "ALL"]:
        # Calling the updated jobs tool with fallback logic
        job_data = match_local_jobs.invoke({"skills": skills, "lat": lat, "lon": lon})
        results_summary.append(f"JOBS_FOUND: {job_data}")
        
    if intent in ["TRAINING", "ALL"]:
        training_data = get_training_programs.invoke({"lat": lat, "lon": lon})
        results_summary.append(f"TRAINING_FOUND: {training_data}")
        
    if intent in ["SHG", "ALL"]:
        shg_data = find_nearby_shgs.invoke({"lat": lat, "lon": lon})
        results_summary.append(f"SHG_FOUND: {shg_data}")

    # 5. Consolidate Findings
    final_findings = "\n".join(results_summary)
    
    return {
        "messages": [AIMessage(content=f"OPPORTUNITY_REPORT:\n{final_findings}")],
        "next_agent": "supervisor"
    }