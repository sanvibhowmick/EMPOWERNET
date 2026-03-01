import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from app.graph.state import AgentState
from app.tools.memory import upsert_user_profile, get_user_context

logger = logging.getLogger(__name__)

class ProfileExtraction(BaseModel):
    """Extracted worker profile information with probabilistic language detection."""
    full_name: Optional[str] = Field(None, description="The user's name")
    district: Optional[str] = Field(None, description="District in UPPERCASE English")
    block: Optional[str] = Field(None, description="Block in UPPERCASE English")
    village: Optional[str] = Field(None, description="Village in UPPERCASE English")
    primary_occupation: Optional[str] = Field(None, description="Job/Skill name")
    # Removed the default value to allow the LLM to choose based on the message script
    language: Optional[str] = Field(
        None, 
        description="The primary language of the user's typing: 'Bengali' or 'English'."
    )

def memory_node(state: AgentState):
    """
    The Memory specialist: Detects language based on script and extracts facts.
    """
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_msg = messages[-1].content if messages else ""

    # A. Load existing profile to maintain continuity
    existing_profile = get_user_context(user_id) or {}
    
    # B. Script-Aware Extraction Logic
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(ProfileExtraction)
    
    # SYSTEM PROMPT: Tells the AI to look at the characters, not the context
    extraction_prompt = (
        f"Analyze this message: '{last_msg}'.\n"
        "1. Identify the language script. If the user uses Bengali characters (like 'আমি'), "
        "set language to 'Bengali'. If they use Latin characters (like 'Hi'), set language to 'English'.\n"
        "2. IMPORTANT: Ignore the language of location IDs (e.g., 'DIST_01') or list button titles. "
        "Only focus on what the user actually typed or intended.\n"
        "3. Extract any location or identity details."
    )
    
    try:
        extracted = structured_llm.invoke(extraction_prompt)
        
        # C. Language Logic: 
        # 1. Use the newly detected language if the AI found one.
        # 2. Otherwise, use the existing profile language.
        # 3. Default to 'English' only if it's a brand new user with no detected script.
        updated_lang = extracted.language or existing_profile.get("language") or "English"
        
        # Merge location facts
        updated_district = extracted.district or existing_profile.get("district")
        updated_block = extracted.block or existing_profile.get("block")
        updated_village = extracted.village or existing_profile.get("village")
        
        # D. Save to DB (Neon/Postgres)
        upsert_user_profile(
            phone_number=user_id,
            name=extracted.full_name or existing_profile.get("full_name"),
            language=updated_lang,
            district=updated_district,
            block=updated_block,
            village=updated_village,
            occupation=extracted.primary_occupation or existing_profile.get("primary_occupation")
        )

        logger.info(f"🧠 Memory Sync: {user_id} | Detected Lang: {updated_lang}")

        # E. Update State for the Swarm
        return {
            "district": updated_district,
            "block": updated_block,
            "village": updated_village,
            "language": updated_lang, 
            "user_name": extracted.full_name or existing_profile.get("full_name", "Friend")
        }

    except Exception as e:
        logger.error(f"❌ Memory Node Error: {e}")
        return {"language": existing_profile.get("language") or "English"}