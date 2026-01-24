from langchain.tools import tool
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

@tool
def get_nearby_training(user_lat: float, user_lon: float, category: str = None):
    """
    Finds active training programs within a 5km radius. 
    Filters by category (e.g., 'Tailoring', 'Computers') if provided.
    """
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Query using ST_DWithin for spatial indexing speed
    query = """
        SELECT title, provider, location_name, duration_weeks,
               ST_Distance(coordinates, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) / 1000 AS dist_km
        FROM training_programs
        WHERE status = 'active'
        AND ST_DWithin(coordinates, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, 5000)
    """
    params = [user_lon, user_lat, user_lon, user_lat]

    if category:
        query += " AND category ILIKE %s"  # Case-insensitive matching
        params.append(f"%{category}%")
    
    query += " ORDER BY dist_km ASC LIMIT 3;"

    try:
        cur.execute(query, tuple(params))
        results = cur.fetchall()
        
        if not results:
            return f"I couldn't find any active {category or ''} training nearby. Should I look for other skills?"

        programs = [f"🎓 {r[0]} ({r[1]}) in {r[2]} - {r[3]} weeks away." for r in results]
        return "\n".join(programs)
    finally:
        cur.close()
        conn.close()