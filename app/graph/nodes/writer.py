from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from app.graph.state import AgentState

def writer_node(state: AgentState, config: RunnableConfig):
    """
    The Writer (Lekhika Didi) node.
    Refines technical specialist output into simple, warm, vernacular speech.
    """
    # 1. Retrieve the context from the State
    technical_report = state["messages"][-1].content
    user_name = state.get("user_name", "Bhon (Sister)")
    lang = state.get("preferred_lang", "Bengali")
    
    # 2. Financial Shield: Use the cheap/fast model for rewriting
    limit = config.get("configurable", {}).get("max_tokens", 400)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4, max_tokens=limit)

    # 3. The Persona-Driven Prompt
    # This prompt forces the AI to think like a community mentor
    system_prompt = f"""
    You are 'Lekhika Didi', a wise and kind elder sister from a village in India. 
    Your goal is to explain the technical info below to {user_name} in very simple {lang}.
    
    GUIDELINES:
    - NO JARGON: Instead of 'Minimum Wage', use 'Sorkari mojuri' (Government pay).
    - EMPATHY: Use warm greetings. Treat her like family.
    - VISUALS: Use emojis like 🌾, ⚖️, or 💰 to help those with low literacy.
    - ANALOGIES: Explain complex ideas using village life examples (e.g., loans are like seeds).
    - ACTIONABLE: Tell her exactly what to do next in one simple sentence.
    
    TECHNICAL INPUT:
    {technical_report}
    """

    # 4. Generate the final friendly response
    final_voice = llm.invoke(system_prompt).content

    print(f"✍️ Writer Node: Finalizing response in {lang} for {user_name}")

    return {
        "messages": [AIMessage(content=final_voice)]
    }