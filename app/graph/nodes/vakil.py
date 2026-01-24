from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.tools.legal import legal_audit_tool
from app.graph.state import AgentState

def vakil_node(state: AgentState):
    """
    The Vakil (Legal Expert) node.
    Uses AI to map user queries to specific labor categories 
    for precise minimum wage auditing from legal PDFs.
    """
    # 1. Get the conversation history
    messages = state.get("messages", [])
    last_user_message = next(
        (m.content for m in reversed(messages) if m.type == "human"), 
        None
    )
    
    if not last_user_message:
        return {"messages": [AIMessage(content="I am ready to help with legal questions.")]}

    # 2. AI Category Extraction (Matching your PDF filenames/content)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    extraction_prompt = (
        "Analyze this worker's query and map it to exactly ONE of these "
        "legal categories found in our records: 'Agriculture', 'Bakery', "
        "'Construction', 'Road Maintenance', or 'Establishment'.\n"
        "Return ONLY the category name. If it does not fit, return 'General'.\n\n"
        f"Worker Message: {last_user_message}"
    )
    
    target_category = llm.invoke(extraction_prompt).content.strip()
    
    print(f"⚖️ Vakil Agent: Identifying legal category as '{target_category}'")

    # 3. Enhanced Tool Invocation
    # We combine the category with the original query for a higher-precision search
    audit_query = f"What is the 2026 minimum wage for {target_category}? {last_user_message}"
    legal_context = legal_audit_tool.invoke(audit_query)

    # 4. Final Response
    # The agent provides a grounded answer based on the PDF data
    response = (
        f"According to the latest 2026 labor standards for the **{target_category}** sector:\n\n"
        f"{legal_context}\n\n"
        "Does your current daily wage match these rates?"
    )

    return {
        "messages": [AIMessage(content=response)],
        "next_agent": "supervisor"
    }