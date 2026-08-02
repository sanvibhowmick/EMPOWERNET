# app/graph/nodes/writer.py

import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.graph.constants import MORE_OPTIONS_ID, MORE_OPTIONS_TITLE, PAGE_SIZE
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


def _build_paginated_rows(raw_items, current_lang, offset):
    """
    FIX (weak point #19): the old code did `raw[:10]`, silently dropping any
    district/block/village beyond the 10th alphabetically -- West Bengal has
    23 districts, so 13 of them were permanently unreachable through the
    WhatsApp menu. WhatsApp interactive lists cap at 10 rows total, so we
    show PAGE_SIZE (9) real items per page plus a 10th "More Options" row
    that advances `location_offset` and re-renders the next page (wrapping
    back to the start once you page past the end).

    Returns (rows_for_this_page_raw_labels, translated_titles).
    """
    if not raw_items:
        return [], []

    start = (offset or 0) * PAGE_SIZE
    if start >= len(raw_items):
        start = 0  # wrap back to page 0 once we've paged past the end

    page = raw_items[start:start + PAGE_SIZE]
    translated_page = translate_ui_items(page, current_lang)

    rows = [{"id": r, "title": t} for r, t in zip(page, translated_page)]

    if len(raw_items) > start + PAGE_SIZE or start > 0:
        # There's more content either ahead or we've wrapped -- always offer
        # a way to keep paging as long as the list didn't fit on one page.
        rows.append({"id": MORE_OPTIONS_ID, "title": MORE_OPTIONS_TITLE})

    return rows


def writer_node(state: AgentState):
    """
    Final Persona Node: Optimized for hierarchical location capture.
    """
    # 1. Source of Truth for Language and Location
    current_lang = state.get("language") or "English"
    district = state.get("district")
    block = state.get("block")
    village = state.get("village")
    offset = state.get("location_offset") or 0

    user_name = state.get("user_name", "Friend")
    messages = state.get("messages", [])
    specialist_report = messages[-1].content if messages else ""

    logger.info(f"✍️ Writer Processing: Lang={current_lang} | D={district} | B={block} | V={village} | Page={offset}")

    # --- 2. HIERARCHICAL UI CHECK ---

    # DISTRICT LEVEL (Must be first)
    if not district:
        raw = get_districts.invoke({})
        rows = _build_paginated_rows(raw, current_lang, offset)
        body = get_localized_ui_text(current_lang, "INTRO_DISTRICT")
        return {"messages": [AIMessage(content="LIST_REQUEST:DISTRICT", additional_kwargs={"rows": rows, "body": body})]}

    # BLOCK LEVEL (Triggers only if District is known)
    if not block:
        raw = get_blocks_for_district.invoke({"district": district})
        rows = _build_paginated_rows(raw, current_lang, offset)
        body = get_localized_ui_text(current_lang, "SELECT_BLOCK", extra_context=district)
        return {"messages": [AIMessage(content="LIST_REQUEST:BLOCK", additional_kwargs={"rows": rows, "body": body})]}

    # VILLAGE LEVEL (Triggers only if Block is known)
    if not village:
        raw = get_villages_for_block.invoke({"block": block})
        rows = _build_paginated_rows(raw, current_lang, offset)
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
