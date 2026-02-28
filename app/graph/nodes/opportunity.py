import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState

# Importing our updated hierarchical tools
from app.tools.jobs import match_local_jobs
from app.tools.training import get_training_programs
from app.tools.community import find_nearby_shgs

logger = logging.getLogger(__name__)

def opportunity_node(state: AgentState):
    """
    The Opportunity Specialist: Triage and Match.
    Uses District, Block, and Village hierarchy to find relevant opportunities.
    """
    # 1. State Recovery & Guarding
    last_msg = state["messages"][-1].content if state.get("messages") else ""
    
    # Recover hierarchical location fields
    district = state.get("district")
    block = state.get("block")
    village = state.get("village")
    
    # Recover skills and skill level
    skills = state.get("user_skills") or "labor"
    skill_level = state.get("skill_level") or "Unskilled"
    
    logger.info(f"🔍 Opportunity Node: Analyzing intent for {skills} in {village}, {block}")

    # 2. Location Check
    # If the hierarchy is incomplete, we cannot run the specific tool queries
    if not district or not block or not village:
        return {
            "messages": [AIMessage(content="OPPORTUNITY_REPORT: Error - Hierarchical location (District/Block/Village) is missing. Please ask the user to select their location via the menu.")],
            "next_agent": "supervisor"
        }

    # 3. Intent Analysis
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    intent_prompt = f"""
    Analyze the user's request: "{last_msg}"
    
    Identify the primary need:
    - 'JOB': User wants to find work, earn money, or see job listings.
    - 'TRAINING': User wants to learn, get a certificate, or join a skill program.
    - 'SHG': User wants to join a group, save money, or find local community circles.
    - 'ALL': If the user is asking a general question like "What is available for me?"
    
    Return ONLY the word: JOB, TRAINING, SHG, or ALL.
    """
    intent = llm.invoke(intent_prompt).content.strip().upper()
    logger.info(f"🎯 Intent Detected: {intent}")

    # 4. Selective Tool Execution using Hierarchy
    results_summary = []

    if intent in ["JOB", "ALL"]:
        # Priority 1: Village match, Priority 2: Skill match
        job_data = match_local_jobs.invoke({
            "skills": skills, 
            "district": district, 
            "block": block, 
            "village": village
        })
        results_summary.append(f"JOBS_FOUND: {job_data}")
        
    if intent in ["TRAINING", "ALL"]:
        # Filters by District and optionally by category (skills)
        training_data = get_training_programs.invoke({
            "district": district, 
            "block": block, 
            "village": village,
            "category": skills
        })
        results_summary.append(f"TRAINING_FOUND: {training_data}")
        
    if intent in ["SHG", "ALL"]:
        # Priority 1: Immediate Village, Priority 2: Nearby in Block
        shg_data = find_nearby_shgs.invoke({
            "district": district, 
            "block": block, 
            "village": village
        })
        results_summary.append(f"SHG_FOUND: {shg_data}")

    # 5. Consolidate Findings
    final_findings = "\n".join(results_summary)
    
    return {
        "messages": [AIMessage(content=f"OPPORTUNITY_REPORT:\n{final_findings}")],
        "next_agent": "supervisor"
    }