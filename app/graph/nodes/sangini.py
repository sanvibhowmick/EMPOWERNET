import logging
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.graph.tools.jobs import match_skills_to_jobs

logger = logging.getLogger(__name__)

def sangini_node(state: AgentState):
    """
    The Sangini (Job Assistant) specialist node.
    Coordinates between user skillsets and geographic/textual location data.
    """
    # 1. Retrieve current message and state variables
    user_query = state["messages"][-1].content
    user_name = state.get("user_name") or "Sister"
    
    # 2. Extract Location and Skill Data
    # These fields should be populated by the Supervisor or DB lookup
    lat = state.get("user_lat")
    lon = state.get("user_lon")
    loc_name = state.get("location_name") # Textual fallback (e.g., 'Bankura')
    
    # Skills extraction from state or query
    skills_raw = state.get("skills") or user_query 

    # 3. FORMATTING FOR THE TOOL (Pydantic Guardrails)
    # Ensures skills is a list and coordinates are floats to prevent validation errors
    skills_list = [skills_raw] if isinstance(skills_raw, str) else skills_raw
    
    try:
        # 4. Invoke the Job Matching Tool
        # Uses GPS if available, otherwise falls back to location_name
        raw_jobs = match_skills_to_jobs.invoke({
            "user_skills": skills_list,
            "user_lat": float(lat) if lat is not None else None,
            "user_lon": float(lon) if lon is not None else None,
            "location_name": loc_name
        })
        
        # 5. Prepare the Technical Report for the Writer Node
        report_header = f"Agent Sangini Report for {user_name}:\n"
        report_body = f"I searched for {skills_list} in {loc_name or 'nearby coordinates'}.\n\n{raw_jobs}"
        report = report_header + report_body
        
    except Exception as e:
        logger.error(f"❌ Sangini Node failed: {str(e)}")
        report = f"Agent Sangini Error: I encountered a problem searching the job database. Please try again later."

    return {
        "messages": [AIMessage(content=report)]
    }