import logging
from langchain_core.tools import tool
# Import your RAG search. Using 'as' lets us use the new name immediately.
from app.core.search import empower_search

logger = logging.getLogger(__name__)

@tool("check_labor_compliance")
def check_labor_compliance(query: str):
    """
    Search the 2026 West Bengal Labor Laws. 
    Use this to audit minimum wages, worker rights, and safety compliance 
    standards for EmpowerNet users.
    """
    try:
        logger.info(f"⚖️ EmpowerNet Compliance: Querying labor laws for: {query}")
        
        
        result = empower_search(query)
        
        if not result:
            return "No specific legal records found in the 2026 labor law database."
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Compliance Tool Error: {e}")
        return f"Database search failed: {str(e)}"