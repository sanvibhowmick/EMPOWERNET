from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes.supervisor import supervisor_node
from app.graph.nodes.memory import memory_node
from app.graph.nodes.vakil import vakil_node
from app.graph.nodes.guru import guru_node
from app.graph.nodes.udyami import udyami_node
from app.graph.nodes.sangini import sangini_node
from app.graph.nodes.chaukas import chaukas_node
from app.graph.nodes.sakhi import sakhi_node
from app.graph.nodes.durga import durga_node
from app.graph.nodes.writer import writer_node
from app.graph.router import graph_router

def build_vesta_swarm():
    """
    Constructs the VESTA Multi-Agent Swarm.
    Flow: User -> Memory -> Supervisor -> Specialist -> Writer -> End
    """
    builder = StateGraph(AgentState)

    # 1. ADD NODES (The Workers)
    builder.add_node("memory", memory_node)      # Updates DB silently
    builder.add_node("supervisor", supervisor_node) # Decides direction
    builder.add_node("vakil", vakil_node)        # Legal
    builder.add_node("guru", guru_node)          # Education
    builder.add_node("udyami", udyami_node)      # Business
    builder.add_node("sangini", sangini_node)    # Jobs
    builder.add_node("chaukas", chaukas_node)    # Reporting
    builder.add_node("sakhi", sakhi_node)        # Safety/General
    builder.add_node("durga", durga_node)        # Emergency Bypass
    builder.add_node("writer", writer_node)      # Persona/Language Filter

    # 2. DEFINE EDGES (The Path)
    
    # Every interaction starts with Memory to ensure we remember the user
    builder.set_entry_point("memory")
    builder.add_edge("memory", "supervisor")

    # The Supervisor uses the 'graph_router' to send the state to a specialist
    builder.add_conditional_edges(
        "supervisor",
        graph_router,
        {
            "vakil": "vakil",
            "guru": "guru",
            "udyami": "udyami",
            "sangini": "sangini",
            "chaukas": "chaukas",
            "sakhi": "sakhi",
            "durga": "durga",    # SOS Bypass
            "end": END
        }
    )

    # ALL specialists send their technical report to the Writer for "humanizing"
    builder.add_edge("vakil", "writer")
    builder.add_edge("guru", "writer")
    builder.add_edge("udyami", "writer")
    builder.add_edge("sangini", "writer")
    builder.add_edge("chaukas", "writer")
    builder.add_edge("sakhi", "writer")

    # Durga and Writer are the final steps
    builder.add_edge("durga", END)
    builder.add_edge("writer", END)

    return builder.compile()

# This is the object you import in main.py
vesta_swarm = build_vesta_swarm()