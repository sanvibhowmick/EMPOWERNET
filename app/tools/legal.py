from langchain.tools import tool
from app.core.search import vesta_search

@tool
def legal_audit_tool(query: str):
    """
    Search the 2026 West Bengal Labor Laws. Use this to check 
    minimum wages, worker rights, and legal safety standards.
    """
    return vesta_search(query)