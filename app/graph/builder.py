# app/graph/builder.py

import logging
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState

from app.graph.nodes.memory import memory_node
from app.graph.nodes.supervisor import supervisor_node
from app.graph.nodes.legal import legal_node
from app.graph.nodes.reporting import reporting_node
from app.graph.nodes.opportunity import opportunity_node
from app.graph.nodes.writer import writer_node

logger = logging.getLogger(__name__)

builder = StateGraph(AgentState)

builder.add_node("memory", memory_node)           # Fact extraction & DB retrieval
builder.add_node("supervisor", supervisor_node)   # Routing & Location Guard
builder.add_node("legal", legal_node)             # Wage & Rights Specialist
builder.add_node("reporting", reporting_node)     # Safety & Site Penalty Specialist
builder.add_node("opportunity", opportunity_node) # Job & Training Specialist
builder.add_node("writer", writer_node)           # Multilingual Persona & Formatting


builder.set_entry_point("memory")

builder.add_edge("memory", "supervisor")


builder.add_conditional_edges(
    "supervisor",
    lambda x: x["next_agent"],
    {
        "legal": "legal",
        "reporting": "reporting",
        "opportunity": "opportunity",
        "writer": "writer",
        "end": END
    }
)

builder.add_edge("legal", "supervisor")
builder.add_edge("reporting", "supervisor")
builder.add_edge("opportunity", "supervisor")


builder.add_edge("writer", END)


# ---------------------------------------------------------------------------
# FIX (weak point #1): main.py passes a `thread_id` into the graph's config
# and its comments call this "persistent memory," but `builder.compile()`
# previously took no `checkpointer=`, so LangGraph had nothing to actually
# persist between separate `invoke()` calls -- every WhatsApp message ran the
# graph completely fresh. The only real continuity came from re-reading the
# Postgres `user_profile` table at the top of `memory_node` every turn.
#
# We now wire a real checkpointer so `thread_id` does what the code already
# claimed it did: the graph's own state (messages, routing decisions, etc.)
# persists per phone number across turns, not just the hand-picked profile
# fields that `memory_node` chooses to save.
#
# Preferred: PostgresSaver, backed by the same Neon database everything else
# uses, so state actually survives process restarts/redeploys.
#   pip install langgraph-checkpoint-postgres
#   (one-time) checkpointer.setup()  -- creates the checkpoint tables
#
# Fallback: MemorySaver, so the graph still has *working* short-term memory
# during local development / if the Postgres checkpoint tables haven't been
# provisioned yet -- this is strictly better than "no checkpointer at all,"
# but does NOT survive a process restart, so it's a dev-mode fallback only.
# ---------------------------------------------------------------------------
def _build_checkpointer():
    from app.core.db import DB_URL

    if DB_URL:
        try:
            from langgraph.checkpoint.postgres import PostgresSaver

            cm = PostgresSaver.from_conn_string(DB_URL)
            checkpointer = cm.__enter__()  # keep the underlying connection open for app lifetime
            checkpointer.setup()  # idempotent -- creates checkpoint tables if missing
            logger.info("✅ Using PostgresSaver for LangGraph checkpointing.")
            return checkpointer
        except Exception as e:
            logger.warning(
                f"⚠️ Could not initialize PostgresSaver ({e}); "
                f"falling back to in-memory checkpointing. Install "
                f"'langgraph-checkpoint-postgres' and ensure DATABASE_URL is "
                f"reachable to get durable, cross-restart conversation memory."
            )

    from langgraph.checkpoint.memory import MemorySaver
    logger.warning(
        "⚠️ Using MemorySaver -- conversation-level graph state will NOT "
        "survive a process restart. This is a dev-mode fallback only."
    )
    return MemorySaver()


_checkpointer = _build_checkpointer()

empower_swarm = builder.compile(checkpointer=_checkpointer)
