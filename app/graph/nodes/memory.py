import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from app.graph.state import AgentState
from app.tools.memory import upsert_user_profile, get_user_context

logger = logging.getLogger(__name__)

class ProfileExtraction(BaseModel):
    """Extracted worker profile information with hierarchical awareness."""
    full_name: Optional[str] = Field(None, description="The user's name")
    district: Optional[str] = Field(None, description="District in UPPERCASE English")
    block: Optional[str] = Field(None, description="Block in UPPERCASE English")
    village: Optional[str] = Field(None, description="Village in UPPERCASE English")
    primary_occupation: Optional[str] = Field(None, description="Job/Skill name")
    language: Optional[str] = Field(
        None, 
        description="The primary script: 'Bengali' or 'English'."
    )

def memory_node(state: AgentState):
    """
    The Memory Specialist: Maps selections to the correct hierarchy level.
    """
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_msg = messages[-1].content if messages else ""

    # A. Get existing context to know where we are in the hierarchy
    existing_profile = get_user_context(user_id) or {}
    has_district = existing_profile.get("district") is not None
    has_block = existing_profile.get("block") is not None
    
    # B. AI Extraction
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(ProfileExtraction)
    
    # THE FIX: Contextual Prompting
    # We tell the AI what we already know so it fills the NEXT logical slot.
    extraction_prompt = (
        f"Analyze the input: '{last_msg}'.\n"
        f"CONTEXT: The user is in District: {existing_profile.get('district')}. "
        f"Current Block: {existing_profile.get('block')}.\n"
        "RULES:\n"
        "1. If we have a District but NO Block, and the user sends a location like 'BARUIPUR', "
        "save it as the 'block'.\n"
        "2. Only save as 'village' if we already have a Block saved.\n"
        "3. Detect language: 'English' for Latin script, 'Bengali' for Bengali script."
    )
    
    try:
        extracted = structured_llm.invoke(extraction_prompt)
        
        # C. Merge Logic: Prioritize new extraction but keep parents
        updated_district = extracted.district or existing_profile.get("district")
        
        # Smart Slotting: If AI thought it was a village but we need a block, move it
        if has_district and not has_block and extracted.village:
             updated_block = extracted.village # Correct the 'Baruipur' mistake
             updated_village = None
        else:
             updated_block = extracted.block or existing_profile.get("block")
             updated_village = extracted.village or existing_profile.get("village")

        updated_lang = extracted.language or existing_profile.get("language") or "English"
        
        # D. Save to DB
        upsert_user_profile(
            phone_number=user_id,
            name=extracted.full_name or existing_profile.get("full_name"),
            language=updated_lang,
            district=updated_district,
            block=updated_block,
            village=updated_village,
            occupation=extracted.primary_occupation or existing_profile.get("primary_occupation")
        )

        logger.info(f"🧠 Memory Sync: {user_id} | Lang: {updated_lang} | D: {updated_district} | B: {updated_block} | V: {updated_village}")

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