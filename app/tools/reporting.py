import os
import logging
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Handle Postgres URL for Neon/SQLAlchemy compatibility
raw_url = os.getenv("DATABASE_URL", "")
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(raw_url)

@tool("submit_safety_report")
def submit_safety_report(user_id: str, description: str, category: str, lat: float, lon: float):
    """
    Logs a safety complaint in English and automatically updates the safety score 
    of nearby vetted job sites (within 500m).
    """
    
    # 1. SQL to insert the report (Description is pre-translated to English by the node)
    insert_query = text("""
        INSERT INTO safety_reports (user_id, description, category, lat, lon, reported_at)
        VALUES (:uid, :desc, :cat, :lat, :lon, CURRENT_TIMESTAMP)
        RETURNING id;
    """)
    
    # 2. SQL to penalize nearby job sites
    # Reduces safety_score by 0.5. Score is capped at a minimum of 1.0.
    update_score_query = text("""
        UPDATE vetted_jobs
        SET safety_score = GREATEST(1.0, safety_score - 0.5)
        WHERE ST_DWithin(location_geog, ST_MakePoint(:lon, :lat)::geography, 500);
    """)
    
    try:
        # Use a transaction block to ensure both operations succeed or both fail
        with engine.begin() as conn:
            # Execute the insert
            result = conn.execute(insert_query, {
                "uid": user_id, 
                "desc": description, 
                "cat": category, 
                "lat": lat, 
                "lon": lon
            })
            report_id = result.fetchone()[0]
            
            # Execute the score update
            update_result = conn.execute(update_score_query, {"lat": lat, "lon": lon})
            affected_sites = update_result.rowcount
            
            logger.info(f"🚩 Safety Report #{report_id} logged in English. {affected_sites} nearby sites penalized.")
            
            return {
                "status": "success",
                "report_id": report_id,
                "sites_impacted": affected_sites,
                "message": f"Report successfully filed. Safety scores for {affected_sites} nearby work sites have been adjusted."
            }

    except Exception as e:
        logger.error(f"❌ Reporting Tool Failure: {e}")
        return {
            "status": "error",
            "message": f"Database transaction failed: {str(e)}"
        }