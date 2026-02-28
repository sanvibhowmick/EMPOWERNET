# app/graph/nodes/writer.py

import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.tools.spatial import get_districts, get_blocks_for_district, get_villages_for_block

logger = logging.getLogger(__name__)

def translate_ui_items(items, target_lang):
    """
    Uses a fast LLM to translate database keys (districts/blocks/villages) 
    into the user's preferred script dynamically.
    """
    if target_lang == "English":
        return items  # Return original English database keys
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = (
        f"Translate the following West Bengal administrative names into {target_lang} script: "
        f"{', '.join(items)}. Return ONLY the translated names separated by commas."
    )
    
    try:
        translated_str = llm.invoke(prompt).content
        return [t.strip() for t in translated_str.split(",")]
    except Exception as e:
        logger.error(f"❌ UI Translation failed: {e}")
        return items  # Fallback to English keys to prevent crash

def writer_node(state: AgentState):
    """
    Final Persona Node: Translates UI dropdowns and specialist findings 
    into a warm, neighborly response for rural women in West Bengal.
    """
    # 1. Capture State & Context
    language = state.get("preferred_lang", "Bengali")
    user_name = state.get("user_name", "Friend")
    district = state.get("district")
    block = state.get("block")
    village = state.get("village")
    
    # Capture the technical finding from the Specialist (Job, Legal, or Training)
    messages = state.get("messages", [])
    specialist_report = messages[-1].content if messages else "hi"

    # --- 2. HIERARCHICAL UI CHECK (DROPDOWNS) ---
    # If location is missing, we trigger the WhatsApp List UI instead of persona text.

    if not district:
        raw = get_districts.invoke({})[:10]
        trans = translate_ui_items(raw, language)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = "নমস্কার! আপনার জেলাটি নির্বাচন করুন:" if language == "Bengali" else "Welcome! Please select your district:"
        return {"messages": [AIMessage(content="LIST_REQUEST:DISTRICT", additional_kwargs={"rows": rows, "body": body})]}
    
    if not block:
        raw = get_blocks_for_district.invoke({"district": district})[:10]
        trans = translate_ui_items(raw, language)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = f"আপনি {district}-এর কোন ব্লকে থাকেন?" if language == "Bengali" else f"Which block in {district} do you live in?"
        return {"messages": [AIMessage(content="LIST_REQUEST:BLOCK", additional_kwargs={"rows": rows, "body": body})]}

    if not village:
        raw = get_villages_for_block.invoke({"block": block})[:10]
        trans = translate_ui_items(raw, language)
        rows = [{"id": r, "title": t} for r, t in zip(raw, trans)]
        body = "আপনার গ্রামটি নির্বাচন করুন:" if language == "Bengali" else "Please select your village:"
        return {"messages": [AIMessage(content="LIST_REQUEST:VILLAGE", additional_kwargs={"rows": rows, "body": body})]}

    # --- 3. DYNAMIC NEIGHBORLY PERSONA ---
    # Once location is fully known, the bot provides warm, local advice.
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    # Specialist report handling: ensure no technical jargon reaches the user.
    persona_prompt = f"""
    You are the EmpowerNet Assistant, acting as a supportive neighbor for women in rural West Bengal. 
    Your goal is to explain things simply and warmly.

    TECHNICAL FINDINGS:
    "{specialist_report}"

    STRICT VOICE RULES:
    1. GREETING: Always start with a warm 'Nomoskar' (নমস্কার) if in Bengali, or 'Hello' if in English.
    2. THE "SPECIALIST" RULE: Never mention 'specialists', 'agents', or 'technical data'. 
       - Instead of: "The specialist says...", Say: "I found some information for you..." 
    3. LANGUAGE: Use {language} script ONLY. 
    4. SIMPLICITY: Use words a neighbor would use. You are talking to rural women.
       - Instead of 'Minimum Wage', say 'the lowest pay the law allows'.
       - Instead of 'Vocational Training', say 'learning a new skill for work'.
    5. HANDLING GENERIC INPUT: If the findings are just "hi" or empty, do not be technical.
       - Instead, say: "Nomoskar {user_name}! I am here to help you find good jobs, check your pay, or learn about women's groups (SHGs) here in {district}."
    6. LOCATION: Acknowledge you are looking specifically for info in {village or block or district}.
    7. EMPATHY: Always end with a supportive note, like "I hope this helps you and your family!" or "Let me know if you want to learn about something else!"
    """

    logger.info(f"✍️ Writer Node: Relaying data for {user_name} in {language}")
    response = llm.invoke(persona_prompt)
    
    return {"messages": [AIMessage(content=response.content)]}