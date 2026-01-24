from langchain.tools import tool
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

@tool
def get_nearby_safety_resources(user_lat: float, user_lon: float, radius_km: float = 1.0):
    """
    Finds the 5 nearest 'Safety Sisters' or emergency resources within a radius.
    Use this tool whenever a user triggers an SOS or feels unsafe walking.
    """
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Optimized PostGIS query for your 'user_profiles' and 'spatial_data' tables
    query = """
        SELECT name, type, 
               ST_Distance(location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) / 1000 AS distance_km
        FROM spatial_resources
        WHERE ST_DWithin(location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
        ORDER BY distance_km
        LIMIT 5;
    """
    
    try:
        # Distance parameter is in meters for ST_DWithin
        cur.execute(query, (user_lon, user_lat, user_lon, user_lat, radius_km * 1000))
        results = cur.fetchall()
        
        if not results:
            return "No nearby resources found within 1km. Broadening search to 5km."

        resources = [f"📍 {r[0]} ({r[1]}) - {round(r[2], 2)} km away" for r in results]
        return "\n".join(resources)

    except Exception as e:
        return f"Spatial Tool Error: {str(e)}"
    finally:
        cur.close()
        conn.close()