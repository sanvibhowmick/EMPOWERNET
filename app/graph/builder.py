from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.router import get_supervisor_router  # Import your AI router logic
from app.graph.nodes.supervisor import supervisor_node
from app.graph.nodes.vakil import vakil_node
from app.graph.nodes.guru import guru_node
from app.graph.nodes.udyami import udyami_node
from app.graph.nodes.sangini import sangini_node
from app.graph.nodes.sakhi import sakhi_node
from app.graph.nodes.chaukas import chaukas_node
from app.graph.nodes.durga import durga_node
from app.core.guard import is_emergency

def graph_router(state: AgentState):
    """
    The central routing logic. 
    Checks guard.py first, then uses your router.py AI decision.
    """
    last_msg = state.get("messages", [])[-1].content if state.get("messages") else ""

    # 1. EMERGENCY BYPASS
    if is_emergency(last_msg):
        return "durga"

    # 2. AI ROUTING DECISION
    # Calls the logic from your router.py
    next_step = get_supervisor_router(state)
    
    if next_step == "FINISH":
        return "end"
    
    return next_step

# --- BUILD THE GRAPH ---

builder = StateGraph(AgentState)

# 1. Add Nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("vakil", vakil_node)
builder.add_node("guru", guru_node)
builder.add_node("udyami", udyami_node)
builder.add_node("sangini", sangini_node)
builder.add_node("sakhi", sakhi_node)
builder.add_node("chaukas", chaukas_node)
builder.add_node("durga", durga_node)

# 2. Set Entry Point
builder.set_entry_point("supervisor")

# 3. Define Specialist Edges (Specialists always return to Supervisor)
builder.add_edge("vakil", "supervisor")
builder.add_edge("guru", "supervisor")
builder.add_edge("udyami", "supervisor")
builder.add_edge("sangini", "supervisor")
builder.add_edge("sakhi", "supervisor")
builder.add_edge("chaukas", "supervisor")
builder.add_edge("durga", "supervisor")

# 4. Integrate your router.py logic as the Conditional Edge
builder.add_conditional_edges(
    "supervisor",
    graph_router,
    {
        "vakil": "vakil",
        "guru": "guru",
        "udyami": "udyami",
        "sangini": "sangini",
        "sakhi": "sakhi",
        "chaukas": "chaukas",
        "durga": "durga",
        "general": "supervisor",
        "end": END
    }
)

# 5. Compile
vesta_swarm = builder.compile()