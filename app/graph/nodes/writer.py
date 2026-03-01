import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.tools.spatial import get_districts, get_blocks_for_district, get_villages_for_block

logger = logging.getLogger(__name__)

def get_localized_ui_text(language, context_key, extra_context=""):
    """Generates UI text in the script detected by the memory node."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompts = {
        "INTRO_DISTRICT": (
            f"Write a warm greeting for 'EmpowerNet' in {language} script. "
            f"Explain I help with jobs and safety. Ask them to select a district. "
            f"Note: Use ONLY {language} script."
        ),
        "SELECT_BLOCK": f"In {language} script, ask the user which block in {extra_context} they live in.",
        "SELECT_VILLAGE": f"In {language} script, ask the user to select their village from the list."
    }
    
    prompt = prompts.get(context_key, f"Select an option in {language}.")
    try:
        return llm.invoke(prompt).content
    except Exception as e:
        logger.error(f"UI Text Generation failed: {e}")
        return "Please select an option:"

def translate_ui_items(items, target_lang):
    """Translates DB items only if the target_lang is Bengali."""
    if not items or target_lang.lower() == "english":
        return items 
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = (
        f"Translate these names into {target_lang} script: {', '.join(items)}. "
        "Return ONLY the translated names separated by commas."
    )
    
    try:
        translated_str = llm.invoke(prompt).content
        parts = [t.strip() for t in translated_str.split(",")]
        return parts if len(parts) == len(items) else items
    except Exception as e:
        logger.error(f"❌ UI Translation failed: {e}")
        return items

def writer_node(state: AgentState):
    """
    Final Persona Node: Mirrors the detected language perfectly from state.
    """
    # FIX: Prioritize 'language' from memory_node, then 'preferred_lang', then a neutral default.
    current_lang = state.get("language") or state.get("preferred_lang") or "English"
    
    user_name = state.get("user_name", "Friend")
    district = state.get("district")
    block = state.get("block")
    village = state.get("village")
    
    messages = state.get("messages", [])
    # Recover findings from the previous specialist (Legal, Safety, etc.)
    specialist_report = messages[-1].content if messages else ""

    # --- 1. HIERARCHICAL UI (DROPDOWNS) ---
    if not district:
        raw = get_districts.invoke({})[:10]
        trans = translate_ui_items(raw, current_lang)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = get_localized_ui_text(current_lang, "INTRO_DISTRICT")
        return {"messages": [AIMessage(content="LIST_REQUEST:DISTRICT", additional_kwargs={"rows": rows, "body": body})]}
    
    if not block:
        raw = get_blocks_for_district.invoke({"district": district})[:10]
        trans = translate_ui_items(raw, current_lang)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = get_localized_ui_text(current_lang, "SELECT_BLOCK", extra_context=district)
        return {"messages": [AIMessage(content="LIST_REQUEST:BLOCK", additional_kwargs={"rows": rows, "body": body})]}

    if not village:
        raw = get_villages_for_block.invoke({"block": block})[:10]
        trans = translate_ui_items(raw, current_lang)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = get_localized_ui_text(current_lang, "SELECT_VILLAGE")
        return {"messages": [AIMessage(content="LIST_REQUEST:VILLAGE", additional_kwargs={"rows": rows, "body": body})]}

    # --- 2. DYNAMIC PERSONA RESPONSE ---
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    persona_prompt = f"""
    You are the 'EmpowerNet Assistant', a supportive neighbor for women in West Bengal. 
    
    STRICT LANGUAGE RULE:
    The user is speaking {current_lang}. 
    You MUST respond using ONLY {current_lang} script. 

    CONTEXT:
    - User: {user_name}
    - Location: {village}, {block}, {district}
    - Findings: "{specialist_report}"
    """

    logger.info(f"✍️ Writer Node: Responding in {current_lang}")
    response = llm.invoke(persona_prompt)
    
    return {"messages": [AIMessage(content=response.content)]}