# app/graph/nodes/writer.py

import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.tools.spatial import get_districts, get_blocks_for_district, get_villages_for_block

logger = logging.getLogger(__name__)

def get_localized_ui_text(language, context_key, extra_context=""):
    """
    Generates localized UI body text and button labels dynamically.
    Avoids hardcoding strings in the logic.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompts = {
        "INTRO_DISTRICT": (
            f"Write a very warm, neighborly greeting for 'EmpowerNet' in {language} script. "
            "Explain simply that I can help find local jobs, check fair pay, and learn about women's groups. "
            "End by asking them to select their district from the list below. Keep it under 3 sentences."
        ),
        "SELECT_BLOCK": f"In {language} script, kindly ask the user which block in {extra_context} they live in.",
        "SELECT_VILLAGE": f"In {language} script, kindly ask the user to select their village from the list."
    }
    
    prompt = prompts.get(context_key, f"Ask the user to select an option in {language}.")
    try:
        return llm.invoke(prompt).content
    except Exception as e:
        logger.error(f"UI Text Generation failed: {e}")
        return "Please select an option:" # Absolute fallback

def translate_ui_items(items, target_lang):
    """
    Translates database keys into the user's preferred script.
    """
    if target_lang == "English":
        return items 
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = (
        f"Translate these West Bengal administrative names into {target_lang} script: "
        f"{', '.join(items)}. Return ONLY the translated names separated by commas."
    )
    
    try:
        translated_str = llm.invoke(prompt).content
        return [t.strip() for t in translated_str.split(",")]
    except Exception as e:
        logger.error(f"❌ UI Translation failed: {e}")
        return items

def writer_node(state: AgentState):
    """
    Final Persona Node: Dynamically generates localized UI and responses.
    """
    language = state.get("preferred_lang", "Bengali")
    user_name = state.get("user_name", "Friend")
    district = state.get("district")
    block = state.get("block")
    village = state.get("village")
    
    messages = state.get("messages", [])
    specialist_report = messages[-1].content if messages else "hi"

    # --- 2. HIERARCHICAL UI CHECK (DROPDOWNS) ---

    # DISTRICT LEVEL (Includes the Warm Intro)
    if not district:
        raw = get_districts.invoke({})[:10]
        trans = translate_ui_items(raw, language)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = get_localized_ui_text(language, "INTRO_DISTRICT")
        return {"messages": [AIMessage(content="LIST_REQUEST:DISTRICT", additional_kwargs={"rows": rows, "body": body})]}
    
    # BLOCK LEVEL
    if not block:
        raw = get_blocks_for_district.invoke({"district": district})[:10]
        trans = translate_ui_items(raw, language)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = get_localized_ui_text(language, "SELECT_BLOCK", extra_context=district)
        return {"messages": [AIMessage(content="LIST_REQUEST:BLOCK", additional_kwargs={"rows": rows, "body": body})]}

    # VILLAGE LEVEL
    if not village:
        raw = get_villages_for_block.invoke({"block": block})[:10]
        trans = translate_ui_items(raw, language)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = get_localized_ui_text(language, "SELECT_VILLAGE")
        return {"messages": [AIMessage(content="LIST_REQUEST:VILLAGE", additional_kwargs={"rows": rows, "body": body})]}

    # --- 3. DYNAMIC NEIGHBORLY PERSONA ---
    # Once location is known, generate the final advice.
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    persona_prompt = f"""
    You are the EmpowerNet Assistant, a supportive neighbor for women in rural West Bengal. 
    
    USER CONTEXT:
    - Name: {user_name}
    - Location: {village}, {block}, {district}
    - Findings to explain: "{specialist_report}"

    STRICT VOICE RULES:
    1. GREETING: Start with a warm localized greeting (e.g., 'Nomoskar' for Bengali).
    2. NO JARGON: Never mention 'specialists' or 'technical data'. Say "I found this for you".
    3. LANGUAGE: Use {language} script ONLY. 
    4. SIMPLICITY: Explain technical things (like minimum wage or vocational training) in simple, neighborly terms.
    5. EMPATHY: End with a supportive note about their family or future.
    """

    logger.info(f"✍️ Writer Node: Relaying data for {user_name} in {language}")
    response = llm.invoke(persona_prompt)
    
    return {"messages": [AIMessage(content=response.content)]}