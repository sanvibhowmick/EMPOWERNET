# app/graph/state.py

from typing import Annotated, Sequence, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    The unified state for the EmpowerNet Swarm.
    Tracks conversation history and hierarchical user context.
    """

    # 1. Conversation History
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 2. User Core Info
    user_id: str
    user_name: Optional[str]
    language: Optional[str]  # e.g., 'Bengali', 'Hindi', 'English'

    # 3. Hierarchical Location (Selected via WhatsApp menus)
    district: Optional[str]        # e.g., '24 PARGANAS NORTH'
    block: Optional[str]           # e.g., 'AMDANGA'
    village: Optional[str]         # e.g., 'ADHATA'

    # 4. Professional Context
    user_skills: Optional[str]
    skill_level: Optional[str]     # 'Unskilled', 'Semi-Skilled', 'Skilled', 'Highly Skilled'

    # 5. Technical Context
    lat: Optional[float]           # Optional backup for geo-fencing
    lon: Optional[float]

    # 6. Routing Context
    next_agent: Optional[str]

    # FIX (weak point #3): explicit, typed signal that a specialist node has
    # finished and produced a report -- replaces the old approach of the
    # supervisor sniffing the last message's text for the substring
    # "SUMMARY"/"REPORT"/"FINDINGS", which only worked by coincidence (every
    # specialist's signal string happened to contain one of those words).
    # Every specialist node now sets this explicitly to True when it's done;
    # the supervisor reads it and resets it to False after routing to writer.
    specialist_done: Optional[bool]

    # FIX (weak point #19): WhatsApp interactive lists can only show 10 rows
    # at once, but West Bengal has 23 districts (and some districts have more
    # than 9 blocks/villages). Instead of silently truncating with `[:10]`
    # and making the rest permanently unreachable, the writer now paginates:
    # it shows 9 real options + a "More options" row, and this offset tracks
    # which page the user is currently on for the level they're selecting.
    location_offset: Optional[int]
