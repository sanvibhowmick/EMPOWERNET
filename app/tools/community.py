from langchain.tools import tool
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

@tool
def get_nearby_shgs(user_lat: float, user_lon: float, radius_km: float = 2.0):
    """
    Finds Self-Help Groups (SHGs) within a specific radius of the worker.
    Use this to connect women to community savings, micro-loans, and collective support.
    """
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Spatial query using PostGIS for precise village-level matching
    query = """
        SELECT name, focus_area, leader_name, contact_number,
               ST_Distance(location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) / 1000 AS dist_km
        FROM self_help_groups
        WHERE ST_DWithin(location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
        ORDER BY dist_km ASC;
    """

    try:
        cur.execute(query, (user_lon, user_lat, user_lon, user_lat, radius_km * 1000))
        results = cur.fetchall()
        
        if not results:
            return "No nearby Self-Help Groups found. I can help you learn how to start a new one with your neighbors!"

        shg_list = [
            f"🤝 {r[0]} ({r[1]}) - Led by {r[2]}. Distance: {round(r[4], 2)}km. Contact: {r[3]}" 
            for r in results
        ]
        
        return "\n".join(shg_list)
    finally:
        cur.close()
        conn.close()