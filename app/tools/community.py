import os
import logging
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

raw_url = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
engine = create_engine(raw_url)

@tool("find_nearby_shgs")
def find_nearby_shgs(lat: float, lon: float):
    """
    Locates Self-Help Groups (SHGs) and community circles nearby.
    If none are within 5km, finds the closest group available.
    """
    query = text("""
        WITH local_shgs AS (
            SELECT shg_name, leader_name, 
                   ST_Distance(location_geog, ST_MakePoint(:lon, :lat)::geography) as dist_m,
                   'Local' as source
            FROM self_help_groups
            WHERE ST_DWithin(location_geog, ST_MakePoint(:lon, :lat)::geography, 5000)
        ),
        fallback_shgs AS (
            SELECT shg_name, leader_name, 
                   ST_Distance(location_geog, ST_MakePoint(:lon, :lat)::geography) as dist_m,
                   'Statewide' as source
            FROM self_help_groups
            WHERE NOT EXISTS (SELECT 1 FROM local_shgs)
            ORDER BY dist_m ASC
            LIMIT 1
        )
        SELECT * FROM local_shgs
        UNION ALL
        SELECT * FROM fallback_shgs
        ORDER BY dist_m ASC;
    """)
    
    try:
        with engine.connect() as conn:
            res = conn.execute(query, {"lat": lat, "lon": lon}).fetchall()
            if not res: 
                return "No registered SHGs found in the system yet."
            
            return [{
                "name": r[0], 
                "contact": r[1], 
                "distance": f"{int(r[2])}m" if r[3] == 'Local' else f"{round(r[2]/1000, 1)}km",
                "type": r[3]
            } for r in res]
    except Exception as e:
        logger.error(f"Community Tool Error: {e}")
        return "Error searching for community groups."