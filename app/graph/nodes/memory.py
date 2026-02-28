# app/graph/nodes/memory.py

import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from app.graph.state import AgentState
from app.tools.memory import upsert_user_profile, get_user_context

logger = logging.getLogger(__name__)

# 1. Define the Schema for AI Extraction
class ProfileExtraction(BaseModel):
    """Extracted worker profile information."""
    full_name: Optional[str] = Field(None, description="The user's name")
    district: Optional[str] = Field(None, description="District in UPPERCASE English")
    block: Optional[str] = Field(None, description="Block in UPPERCASE English")
    village: Optional[str] = Field(None, description="Village in UPPERCASE English")
    primary_occupation: Optional[str] = Field(None, description="Job/Skill name")
    preferred_lang: str = Field(
        "Bengali", 
        description="Detected language of the message: 'Bengali' or 'English'"
    )

def memory_node(state: AgentState):
    """
    The Memory specialist: Detects language and extracts location/skills.
    Uses Structured Output to prevent JSON parsing crashes.
    """
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_msg = messages[-1].content if messages else ""

    # A. Load existing profile to prevent overwriting known data
    existing_profile = get_user_context(user_id) or {}
    
    # B. AI Extraction using Structured Output
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(ProfileExtraction)
    
    try:
        # The AI now returns a 'ProfileExtraction' object directly
        extracted = structured_llm.invoke(f"Extract profile from: {last_msg}")
        
        # C. Logic: Merge New Facts with Existing Data
        # We prioritize existing data if the new extraction is null
        updated_district = extracted.district or existing_profile.get("district")
        updated_block = extracted.block or existing_profile.get("block")
        updated_village = extracted.village or existing_profile.get("village")
        updated_lang = extracted.preferred_lang # AI is excellent at detecting 'Nomoskar' = Bengali
        
        # D. Save to Neon/Postgres
        upsert_user_profile(
            phone_number=user_id,
            name=extracted.full_name or existing_profile.get("full_name"),
            language=updated_lang,
            district=updated_district,
            block=updated_block,
            village=updated_village,
            occupation=extracted.primary_occupation or existing_profile.get("primary_occupation")
        )

        logger.info(f"🧠 Memory Sync: {user_id} | Lang: {updated_lang} | Dist: {updated_district}")

        # E. Update State for the Supervisor and Writer
        return {
            "district": updated_district,
            "block": updated_block,
            "village": updated_village,
            "preferred_lang": updated_lang,
            "user_name": extracted.full_name or existing_profile.get("full_name", "Friend")
        }

    except Exception as e:
        logger.error(f"❌ Structured Extraction Error for {user_id}: {e}")
        # Fallback to existing state if extraction fails
        return {
            "preferred_lang": existing_profile.get("preferred_lang", "Bengali")
        }