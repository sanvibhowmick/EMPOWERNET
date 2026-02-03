import os
import logging
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

raw_url = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
engine = create_engine(raw_url)

@tool("get_training_programs")
def get_training_programs(lat: float, lon: float):
    """
    Finds nearby government training and skill development programs.
    If none are in the local block, finds the closest program in the state.
    """
    query = text("""
        WITH local_training AS (
            SELECT program_name, agency, enrollment_deadline,
                   ST_Distance(location_geog, ST_MakePoint(:lon, :lat)::geography) / 1000 as dist_km,
                   'Local' as source
            FROM training_programs
            WHERE ST_DWithin(location_geog, ST_MakePoint(:lon, :lat)::geography, 15000)
        ),
        fallback_training AS (
            SELECT program_name, agency, enrollment_deadline,
                   ST_Distance(location_geog, ST_MakePoint(:lon, :lat)::geography) / 1000 as dist_km,
                   'Statewide' as source
            FROM training_programs
            WHERE NOT EXISTS (SELECT 1 FROM local_training)
            ORDER BY dist_km ASC
            LIMIT 1
        )
        SELECT * FROM local_training
        UNION ALL
        SELECT * FROM fallback_training
        ORDER BY dist_km ASC;
    """)
    
    try:
        with engine.connect() as conn:
            res = conn.execute(query, {"lat": lat, "lon": lon}).fetchall()
            if not res: 
                return "No training programs currently available in the database."
            
            return [{
                "program": r[0], 
                "agency": r[1], 
                "deadline": str(r[2]), 
                "distance_km": round(r[3], 1),
                "type": r[4]
            } for r in res]
    except Exception as e:
        logger.error(f"Training Tool Error: {e}")
        return "Could not retrieve training programs at this time."