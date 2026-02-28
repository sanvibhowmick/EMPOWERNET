
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState

from app.graph.nodes.memory import memory_node
from app.graph.nodes.supervisor import supervisor_node
from app.graph.nodes.legal import legal_node
from app.graph.nodes.reporting import reporting_node
from app.graph.nodes.opportunity import opportunity_node
from app.graph.nodes.writer import writer_node


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

empower_swarm = builder.compile()