from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes.memory import memory_node
from app.graph.nodes.supervisor import supervisor_node
from app.graph.nodes.legal import legal_node
from app.graph.nodes.reporting import reporting_node
from app.graph.nodes.opportunity import opportunity_node
from app.graph.nodes.writer import writer_node

builder=StateGraph(AgentState)
builder.add_node("memory", memory_node, transitions={"next": "supervisor"})
builder.add_node("supervisor", supervisor_node)   
builder.add_node("legal", legal_node)             
builder.add_node("reporting", reporting_node)     
builder.add_node("opportunity", opportunity_node)
builder.add_node("writer", writer_node)           

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