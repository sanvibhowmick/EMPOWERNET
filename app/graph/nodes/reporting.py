import logging
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.tools.spatial import get_districts, get_blocks_for_district, get_villages_for_block

logger = logging.getLogger(__name__)

def detect_language(messages):
    """
    Detects if the user is typing in English or a local script.
    """
    last_user_msg = ""
    for m in reversed(messages):
        if not isinstance(m, AIMessage):
            last_user_msg = m.content
            break
    
    # Check for English alphabets (Latin script)
    if re.search(r'[a-zA-Z]', last_user_msg):
        return "English"
    return "Bengali"

def get_localized_ui_text(language, context_key, extra_context=""):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompts = {
        "INTRO_DISTRICT": (
            f"Write a very warm, neighborly greeting for 'EmpowerNet' in {language}. "
            "Explain that EmpowerNet helps women find local job opportunities, understand their legal rights (like maternity benefits and fair wages), "
            "and connect with local self-help groups. "
            "Then, kindly ask them to select their district to see services near them. Keep it under 3-4 sentences."
        ),
        "SELECT_BLOCK": f"In {language}, kindly ask which block in {extra_context} they live in.",
        "SELECT_VILLAGE": f"In {language}, ask the user to select their village so I can find the best local groups and jobs for them."
    }
    
    prompt = prompts.get(context_key, f"Ask the user to select an option in {language}.")
    try:
        return llm.invoke(prompt).content
    except Exception as e:
        logger.error(f"UI Text Generation failed: {e}")
        return "Please select an option:"

def translate_ui_items(items, target_lang):
    if target_lang == "English":
        return items 
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = (
        f"Translate these administrative names into {target_lang} script: "
        f"{', '.join(items)}. Return ONLY comma-separated names. No code, no python."
    )
    
    try:
        translated_str = llm.invoke(prompt).content
        return [t.strip() for t in translated_str.split(",")]
    except Exception as e:
        logger.error(f"❌ UI Translation failed: {e}")
        return items

def writer_node(state: AgentState):
    messages = state.get("messages", [])
    
    # 1. DYNAMIC LANGUAGE DETECTION
    language = detect_language(messages)
    user_name = state.get("user_name", "Friend")
    
    district = state.get("district")
    block = state.get("block")
    village = state.get("village")
    
    # Check if location data is incomplete to trigger onboarding
    is_new_user = not (district and block and village)
    
    specialist_report = messages[-1].content if messages else ""

    # 2. SELECTIVE LOCATION GATHERING
    # Force dropdowns if location is missing OR specialist mentions spatial data/greetings
    spatial_keywords = ["job", "wage", "training", "scheme", "block", "village", "district", "hello", "hi"]
    needs_spatial_data = any(word in specialist_report.lower() for word in spatial_keywords) or is_new_user

    if needs_spatial_data:
        # DISTRICT LEVEL (Introductory Message happens here)
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

    # 3. DYNAMIC NEIGHBORLY PERSONA
    # Respond naturally if location is complete or no specific spatial query is active
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    persona_prompt = f"""
    You are the EmpowerNet Assistant, a supportive neighbor. 
    
    USER CONTEXT:
    - Name: {user_name}
    - Location: {village or 'Not specified'}, {block or ''}, {district or ''}
    - Findings: "{specialist_report}"

    STRICT VOICE RULES:
    1. GREETING: Warm greeting in {language}.
    2. LANGUAGE: Use {language} script ONLY. 
    3. NO METADATA: Do not mention 'LIST_REQUEST' or 'Specialist'. 
    4. SIMPLICITY: Explain everything like you're talking to a sister.
    """

    response = llm.invoke(persona_prompt)
    return {"messages": [AIMessage(content=response.content)]}