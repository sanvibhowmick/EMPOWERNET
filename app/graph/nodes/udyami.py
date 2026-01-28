from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from app.tools.community import get_nearby_shgs
from app.tools.memory import get_user_context
from app.graph.state import AgentState

def udyami_node(state: AgentState, config: RunnableConfig):
    """
    The Udyami node.
    Provides business and SHG advice. Location is now optional for general 
    inquiries to reduce user friction.
    """
    user_id = state.get("user_id")
    last_msg = state["messages"][-1].content
    
    print(f"💰 Udyami Agent: Accessing profile for {user_id}...")

    # 1. Retrieve user profile context
    profile = get_user_context.invoke({"phone_number": user_id})
    user_lat = profile.get("lat")
    user_lon = profile.get("lon")

    # 2. Financial Shield: Token and Model Config
    conf = config.get("configurable", {})
    limit = conf.get("max_tokens", 400)
    llm = ChatOpenAI(model=conf.get("model", "gpt-4o-mini"), temperature=0, max_tokens=limit)

    # 3. Location-Optional Logic
    if user_lat and user_lon:
        # User has location: Find real groups nearby
        shg_data = get_nearby_shgs.invoke({"user_lat": user_lat, "user_lon": user_lon})
        location_context = f"The user is at Lat: {user_lat}, Lon: {user_lon}. Nearby groups found: {shg_data}"
    else:
        # No location: Provide general setup and loan advice
        location_context = "User location is unknown. Focus on general SHG formation rules and micro-loan availability in West Bengal."

    # 4. Formulate the empathetic response
    system_prompt = f"""
    You are Udyami Didi, a business mentor for rural women. 
    Use the following context to answer the question: {location_context}

    If location is missing, DO NOT ask for a location pin immediately. 
    Instead, explain how SHGs work or how to apply for a small loan. 
    Only mention sending a location if the user specifically asks 'Where is the nearest group?'.
    
    Question: {last_msg}
    """

    response = llm.invoke(system_prompt).content

    return {
        "messages": [AIMessage(content=response)],
        "next_agent": "writer" # Leads directly to the Lekhika node for humanizing
    }