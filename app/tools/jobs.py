from langchain.tools import tool
import psycopg2
import os

@tool
def match_skills_to_jobs(user_skills: list, user_lat: float, user_lon: float):
    """
    Matches a user's specific skill set (e.g., ['Tailoring', 'Baking']) 
    to vetted jobs within a 5km radius.
    """
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # This query looks for jobs where the 'required_skill' matches the user's list
    # and calculates the distance using PostGIS.
    query = """
        SELECT title, employer_name, daily_wage, 
               ST_Distance(location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) / 1000 AS dist_km
        FROM vetted_jobs
        WHERE required_skill = ANY(%s)
        AND ST_DWithin(location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, 5000)
        ORDER BY dist_km ASC;
    """

    try:
        cur.execute(query, (user_lon, user_lat, user_skills, user_lon, user_lat))
        results = cur.fetchall()
        
        if not results:
            return "No exact skill matches found nearby. Would you like to see all available jobs?"

        matches = [f"⭐ {r[0]} at {r[1]} (Match for your skills!) - ₹{r[2]}/day" for r in results]
        return "\n".join(matches)
    finally:
        cur.close()
        conn.close()