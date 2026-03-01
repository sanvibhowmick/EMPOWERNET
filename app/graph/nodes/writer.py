import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.tools.spatial import get_districts, get_blocks_for_district, get_villages_for_block

logger = logging.getLogger(__name__)

def get_localized_ui_text(language, context_key, extra_context=""):
    """Generates localized UI body text dynamically."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompts = {
        "INTRO_DISTRICT": (
            f"Write a very warm greeting for 'EmpowerNet' in {language} script. "
            "Explain simply that I can help find local jobs and safety aid. "
            "Ask them to select their district from the list below."
        ),
        "SELECT_BLOCK": f"In {language}, kindly ask the user which block in {extra_context} they live in.",
        "SELECT_VILLAGE": f"In {language}, kindly ask the user to select their village from the list."
    }
    
    prompt = prompts.get(context_key, f"Please select an option in {language}:")
    try:
        return llm.invoke(prompt).content
    except Exception as e:
        logger.error(f"UI Text Generation failed: {e}")
        return "Please select an option:"

def translate_ui_items(items, target_lang):
    """Translates database items into the current session language script."""
    if not items or target_lang.lower() == "english":
        return items 
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = (
        f"Translate these West Bengal administrative names into {target_lang} script: "
        f"{', '.join(items)}. Return ONLY the translated names separated by commas."
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
    Final Persona Node: Optimized for hierarchical location capture.
    """
    # 1. Source of Truth for Language and Location
    current_lang = state.get("language") or "English"
    district = state.get("district")
    block = state.get("block")
    village = state.get("village")
    
    user_name = state.get("user_name", "Friend")
    messages = state.get("messages", [])
    specialist_report = messages[-1].content if messages else ""

    logger.info(f"✍️ Writer Processing: Lang={current_lang} | D={district} | B={block} | V={village}")

    # --- 2. HIERARCHICAL UI CHECK ---

    # DISTRICT LEVEL (Must be first)
    if not district:
        raw = get_districts.invoke({})[:10]
        trans = translate_ui_items(raw, current_lang)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = get_localized_ui_text(current_lang, "INTRO_DISTRICT")
        return {"messages": [AIMessage(content="LIST_REQUEST:DISTRICT", additional_kwargs={"rows": rows, "body": body})]}
    
    # BLOCK LEVEL (Triggers only if District is known)
    if not block:
        raw = get_blocks_for_district.invoke({"district": district})[:10]
        trans = translate_ui_items(raw, current_lang)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = get_localized_ui_text(current_lang, "SELECT_BLOCK", extra_context=district)
        return {"messages": [AIMessage(content="LIST_REQUEST:BLOCK", additional_kwargs={"rows": rows, "body": body})]}

    # VILLAGE LEVEL (Triggers only if Block is known)
    if not village:
        raw = get_villages_for_block.invoke({"block": block})[:10]
        trans = translate_ui_items(raw, current_lang)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = get_localized_ui_text(current_lang, "SELECT_VILLAGE")
        return {"messages": [AIMessage(content="LIST_REQUEST:VILLAGE", additional_kwargs={"rows": rows, "body": body})]}

    # --- 3. FINAL NEIGHBORLY PERSONA ---
    # Once all location data is captured, provide the advice
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2) # Low temperature for script strictness
    
    persona_prompt = f"""
    You are the 'EmpowerNet Assistant', a supportive neighbor for women in rural West Bengal.
    
    STRICT RULE:
    Respond ONLY in {current_lang} script. 
    If {current_lang} is English, use NO Bengali characters.

    CONTEXT:
    - Name: {user_name}
    - Location: {village}, {block}, {district}
    - Findings: "{specialist_report}"
    """

    response = llm.invoke(persona_prompt)
    return {"messages": [AIMessage(content=response.content)]}