import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from app.graph.state import AgentState

# Tools
from app.tools.memory import upsert_user_profile, get_user_context
from app.tools.spatial import get_lat_lon_from_name, decode_location_from_coordinates

logger = logging.getLogger(__name__)

class UserFacts(BaseModel):
    """Schema for extracting user details. All text fields should be in English."""
    name: Optional[str] = Field(None, description="User's name in English characters")
    language: Optional[str] = Field(None, description="The language the user is speaking (e.g., Bengali)")
    skills: Optional[str] = Field(None, description="User's professional skills translated to English")
    location: Optional[str] = Field(None, description="Village or city name translated to English")

def memory_node(state: AgentState):
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_msg = messages[-1].content if messages else ""
    
    # 1. LOAD PERSISTED CONTEXT (Data in DB is English)
    db_data = get_user_context(str(user_id)) or {}
    
    # 2. AI FACT EXTRACTION & TRANSLATION
    # We force the LLM to translate everything it finds into English for the DB
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(UserFacts)
    extract_prompt = (
        f"Analyze this message: '{last_msg}'\n"
        "Identify the user's name, skills, and location. "
        "IMPORTANT: Translate all extracted info (skills, location, name) into ENGLISH "
        "regardless of the language used in the message."
    )
    new_facts = llm.invoke(extract_prompt)
    
    # 3. LANGUAGE LOGIC (Detect but don't translate the 'language' label)
    # This stays in the state so the Writer knows the user's preference
    detected_lang = new_facts.language or db_data.get("preferred_lang") or "Bengali"
    script_pref = "Native" if detected_lang != "English" else "English"

    # 4. COORDINATE LOGIC (Using the English location name)
    lat = db_data.get("lat") or state.get("lat")
    lon = db_data.get("lon") or state.get("lon")
    location_name = new_facts.location or db_data.get("location_name") or state.get("location_name")

    if new_facts.location:
        coord_str = get_lat_lon_from_name.invoke({"location_name": new_facts.location})
        if coord_str and "None" not in coord_str:
            try:
                lat, lon = map(float, coord_str.split(","))
            except: pass
    
    # 5. PERSIST TO DATABASE (Strictly English)
    current_name = new_facts.name or db_data.get("name")
    current_skills = new_facts.skills or db_data.get("skills")

    upsert_user_profile(
        phone_number=str(user_id),
        name=current_name,
        language=detected_lang, # Label (e.g., 'Bengali') is stored in English
        skills=current_skills,  # e.g., 'Nurse' instead of 'সেবিকা'
        lat=lat,
        lon=lon
    )
    
    # 6. UPDATE GLOBAL STATE
    # We return English facts for the Supervisor/Specialists, 
    # but the language pref for the Writer.
    return {
        "user_name": current_name,
        "preferred_lang": detected_lang,
        "preferred_script": script_pref,
        "user_skills": current_skills,
        "location_name": location_name,
        "lat": lat,
        "lon": lon,
        "next_agent": "supervisor"
    }