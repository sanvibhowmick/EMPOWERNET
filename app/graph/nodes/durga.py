from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.tools.spatial import get_nearby_safety_resources
from app.tools.memory import get_user_context
from app.tools.notifications import alert_safety_network # New Tool
from app.graph.state import AgentState

def durga_node(state: AgentState):
    """
    The Durga (Emergency) node. 
    Triggers SOS protocols, notifies the network, and provides panic-reducing guidance.
    """
    user_id = state.get("user_id")
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # 1. Retrieve Dynamic Identity & Location
    profile = get_user_context.invoke({"phone_number": user_id})
    user_lat = profile.get("lat")
    user_lon = profile.get("lon")
    user_name = profile.get("name", "Sister")

    # 2. Urgent Location Guard
    if not user_lat or not user_lon:
        return {
            "messages": [AIMessage(content=(
                f"I am here, {user_name}. Please share your LIVE LOCATION immediately "
                "so I can send help. While you do that, find a bright, crowded place."
            ))],
            "next_agent": "supervisor"
        }

    # 3. Step A: Identify who is nearby
    # We find the 5 closest resources (Police, Shakti Centers, Safety Sisters)
    nearby_help_summary = get_nearby_safety_resources.invoke({
        "user_lat": user_lat, 
        "user_lon": user_lon,
        "radius_km": 1.0 
    })

    # 4. Step B: ACTIVATE THE NETWORK (The Notification)
    # This tool sends actual WhatsApp alerts to the sisters found in Step A
    notification_status = alert_safety_network.invoke({
        "user_name": user_name,
        "user_lat": user_lat,
        "user_lon": user_lon,
        "radius_km": 1.0
    })

    print(f"🚨 ALERT LOG: {notification_status}")

    # 5. AI-Driven Emergency Synthesis
    emergency_prompt = (
        f"You are Durga, the Emergency Response Agent. The user, {user_name}, is in danger. "
        f"We have already notified the nearby Safety Sister network. "
        f"Based on their location, here is the help available:\n\n"
        f"Nearby Help: {nearby_help_summary}\n\n"
        "Instructions: Give them a specific 3-step action plan to stay safe until help arrives. "
        "Be calm and firm."
    )

    response_content = llm.invoke(emergency_prompt).content

    return {
        "messages": [AIMessage(content=response_content)],
        "next_agent": "supervisor"
    }