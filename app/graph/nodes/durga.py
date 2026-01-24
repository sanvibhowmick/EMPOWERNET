from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.tools.spatial import get_nearby_safety_resources
from app.tools.memory import get_user_context
from app.graph.state import AgentState

def durga_node(state: AgentState):
    """
    The Durga (Emergency) node. 
    Triggers SOS protocols, locates nearby help, and provides panic-reducing guidance.
    """
    user_id = state.get("user_id")
    llm = ChatOpenAI(model="gpt-4o", temperature=0) # Use high-reasoning for stress management
    
    # 1. Retrieve Dynamic Identity & Location
    # We use the memory tool to avoid hardcoding JU or Kolkata coords
    profile = get_user_context.invoke({"phone_number": user_id})
    user_lat = profile.get("lat")
    user_lon = profile.get("lon")
    user_name = profile.get("name", "Sister")

    print(f"🚨 DURGA ACTIVATED: Emergency response for {user_id} at {user_lat}, {user_lon}")

    # 2. Call Spatial Tool for immediate physical resources
    # We look for the 5 closest resources (Police, Shakti Centers, Safety Sisters)
    nearby_help = get_nearby_safety_resources.invoke({
        "user_lat": user_lat, 
        "user_lon": user_lon,
        "radius_km": 1.0 # Tight radius for immediate emergency
    })

    # 3. AI-Driven Emergency Synthesis
    # The AI crafts a calm, instruction-heavy response based on actual nearby resources
    emergency_prompt = (
        f"You are Durga, the Emergency Response Agent for VESTA. "
        f"The user, {user_name}, is in immediate danger. Keep your tone calm, firm, and helpful. "
        f"Based on their location, here is the help available:\n\n"
        f"Nearby Help: {nearby_help}\n\n"
        "Instructions: Give them a specific 3-step action plan to reach the nearest safe spot. "
        "Remind them that you are notifying the local Safety Sister network now."
    )

    response_content = llm.invoke(emergency_prompt).content

    return {
        "messages": [AIMessage(content=response_content)],
        "next_agent": "supervisor" # Usually Durga ends the turn or stays in a loop
    }