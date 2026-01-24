from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.tools.skills import match_skills_to_jobs
from app.tools.legal import legal_audit_tool
from app.tools.memory import get_user_context
from app.graph.state import AgentState
import psycopg2
import os

def check_location_safety(lat, lon):
    """Internal helper to query the Chaukas safety database via PostGIS."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    query = """
        SELECT AVG(severity_score) FROM safety_reports 
        WHERE ST_DWithin(location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, 1000)
    """
    cur.execute(query, (lon, lat))
    score = cur.fetchone()[0] or 0.0
    cur.close()
    conn.close()
    return score

def sangini_node(state: AgentState):
    user_id = state.get("user_id")
    llm = ChatOpenAI(model="gpt-4o", temperature=0) # High reasoning for synthesis
    
    # 1. Retrieve Dynamic User Data
    profile = get_user_context.invoke({"phone_number": user_id})
    user_lat, user_lon = profile.get("lat"), profile.get("lon")
    user_skills = profile.get("skills", ["General"])

    # 2. Execute Dynamic Tools
    # Returns real jobs from the 'vetted_jobs' table
    raw_jobs = match_skills_to_jobs.invoke({
        "user_skills": user_skills,
        "user_lat": user_lat,
        "user_lon": user_lon
    })

    # Returns legal grounding from your PDFs (Agriculture, Bakery, Construction, etc.)
    # We pass the raw_jobs to the legal tool so it knows which industry to audit
    wage_audit = legal_audit_tool.invoke(f"What is the minimum wage for the jobs mentioned here: {raw_jobs}")
    
    # Returns real-time safety metrics from the Chaukas DB
    safety_score = check_location_safety(user_lat, user_lon)

    # 3. AI Response Synthesis
    # No more hardcoded "Bakery" or "Safe Area" text
    synthesis_prompt = (
        f"You are Sangini, the Career Partner agent. Using the data below, "
        f"present the best job match to the worker. You MUST mention the legal "
        f"minimum wage audit and the safety status of the area.\n\n"
        f"Worker Skills: {user_skills}\n"
        f"Available Jobs: {raw_jobs}\n"
        f"Legal Audit: {wage_audit}\n"
        f"Safety Score (0=Safe, 1=Danger): {safety_score}\n\n"
        "Instructions: Be empathetic, clear, and professional. Ask the user 'Do you want this?' at the end."
    )

    ai_response = llm.invoke(synthesis_prompt).content

    return {
        "messages": [AIMessage(content=ai_response)],
        "next_agent": "supervisor"
    }