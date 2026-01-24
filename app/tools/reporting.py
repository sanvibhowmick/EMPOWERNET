from langchain.tools import tool
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

@tool
def submit_safety_report(user_id: str, description: str, lat: float, lon: float, severity: float):
    """
    Records a safety complaint or incident in the database. 
    Use this when a woman reports harassment, unsafe areas, or workplace issues.
    """
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    query = """
        INSERT INTO safety_reports (reporter_id, location, description, severity_score)
        VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s, %s)
        RETURNING report_id;
    """

    try:
        cur.execute(query, (user_id, lon, lat, description, severity))
        report_id = cur.fetchone()[0]
        conn.commit()
        return f"Report #{report_id} has been logged. We are monitoring this area."
    except Exception as e:
        return f"Reporting Error: {str(e)}"
    finally:
        cur.close()
        conn.close()