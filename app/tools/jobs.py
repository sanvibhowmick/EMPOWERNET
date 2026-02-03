import os
import logging
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Database Connection
raw_url = os.getenv("DATABASE_URL", "")
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(raw_url)

@tool("match_local_jobs")
def match_local_jobs(skills: str, lat: float, lon: float):
    """
    Finds job openings within 10km of the user based on skills and safety.
    Prioritizes jobs with higher safety scores (safety_score column).
    If no local jobs exist, it finds the closest safe match in the state.
    """
    
    # Clean up input
    search_term = skills if skills and skills.lower() != "none" else "labor"

    # SQL Logic:
    # 1. 'local_jobs' tries the strict 10km radius + Safety Filter (score >= 2.0).
    # 2. 'fallback_jobs' only runs if local_jobs is empty.
    # 3. We use a safety weighted ranking: (safety_score * 2) - (distance / 5)
    query = text("""
        WITH local_jobs AS (
            SELECT title, company, contact_person, safety_score,
                   ST_Distance(location_geog, ST_MakePoint(:lon, :lat)::geography) / 1000 as dist_km,
                   'Local' as source
            FROM vetted_jobs
            WHERE ST_DWithin(location_geog, ST_MakePoint(:lon, :lat)::geography, 10000)
            AND (title ILIKE :skills OR description ILIKE :skills)
            AND safety_score >= 2.0 -- Filter out dangerous workplaces
        ),
        fallback_jobs AS (
            SELECT title, company, contact_person, safety_score,
                   ST_Distance(location_geog, ST_MakePoint(:lon, :lat)::geography) / 1000 as dist_km,
                   'Statewide' as source
            FROM vetted_jobs
            WHERE (title ILIKE :skills OR description ILIKE :skills)
            AND safety_score >= 3.0 -- Fallback only shows high-safety options
            AND NOT EXISTS (SELECT 1 FROM local_jobs)
            ORDER BY dist_km ASC
            LIMIT 1
        )
        SELECT * FROM local_jobs
        UNION ALL
        SELECT * FROM fallback_jobs
        ORDER BY safety_score DESC, dist_km ASC;
    """)
    
    try:
        with engine.connect() as conn:
            res = conn.execute(query, {
                "skills": f"%{search_term}%", 
                "lat": lat, 
                "lon": lon
            }).fetchall()
            
            if not res:
                return f"I couldn't find any safe jobs matching '{search_term}' right now."

            results = []
            for r in res:
                # We normalize the safety score into a user-friendly rating
                safety_rating = "Excellent" if r[3] >= 4.5 else "Good" if r[3] >= 3.5 else "Average"
                
                results.append({
                    "job": r[0],
                    "org": r[1],
                    "contact": r[2],
                    "safety_score": f"{r[3]}/5",
                    "safety_label": safety_rating,
                    "distance_km": round(r[4], 1),
                    "match_type": r[5]
                })
            
            return results

    except Exception as e:
        logger.error(f"❌ Safety-Jobs Tool Error: {e}")
        return f"Database error during job search: {str(e)}"