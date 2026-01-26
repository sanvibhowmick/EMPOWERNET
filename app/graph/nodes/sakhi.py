from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from app.tools.memory import get_user_context
from app.graph.state import AgentState

def sakhi_node(state: AgentState, config: RunnableConfig):
    """
    The Sakhi (Safety & General Help) node.
    Handles greetings and finding 'Safety Sisters' for walks home.
    """
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_msg = messages[-1].content.lower() if messages else ""

    # 1. Financial Shield: Enforce token limit from your main.py config
    limit = config.get("configurable", {}).get("max_tokens", 400)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=limit)

    # 2. Handle Greetings / General Help
    # This ensures a response if the supervisor identifies a 'general' intent
    if any(greet in last_msg for greet in ["hi", "hello", "namaste", "nomoshkar"]):
        response = (
            "Nomoshkar! I am VESTA, your Digital Didi. 🙏\n\n"
            "I can help you with:\n"
            "⚖️ **Vakil**: Check if you are getting paid the right minimum wage.\n"
            "🎓 **Guru**: Find free training programs near you.\n"
            "🤝 **Sangini**: Find safe, community-vetted jobs.\n"
            "🛡️ **Sakhi**: Find a sister to walk home with at night.\n\n"
            "How can I help you today?"
        )
        return {
            "messages": [AIMessage(content=response)],
            "next_agent": "supervisor"
        }

    # 3. Handle Safety Logic (Safety Sister Search)
    # Retrieves user location to find nearby help
    profile = get_user_context.invoke({"phone_number": user_id})
    user_lat, user_lon = profile.get("lat"), profile.get("lon")

    if not user_lat or not user_lon:
        response = "I'm here to help you stay safe, but I couldn't find your location. Please share your Live Location on WhatsApp so I can find sisters near you."
    else:
        # Placeholder for actual safety sister matching logic
        response = (
            f"I see you are at ({user_lat}, {user_lon}). "
            "I'm searching for a Safety Sister to walk with you home. Please wait a moment..."
        )

    return {
        "messages": [AIMessage(content=response)],
        "next_agent": "supervisor"
    }