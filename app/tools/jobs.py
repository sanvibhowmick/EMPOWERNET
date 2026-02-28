# app/tools/jobs.py

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "")
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

@tool("match_local_jobs")
def match_local_jobs(skills: str, district: str, block: str, village: str):
    """
    Finds verified job openings for unorganised sector workers.
    Priority 1: Exact village match.
    Priority 2: Same block.
    Priority 3: Same district or skill keyword match.
    Only returns active jobs.
    """

    search_term = f"%{skills}%" if skills and str(skills).lower() != "none" else "%"

    query = """
        SELECT
            job_title,
            description,
            category,
            district,
            block,
            gram_panchayat,
            village,
            pay_rate_daily,
            duration_days,
            start_date,
            ngo_partner_name,
            contact_person,
            contact_number,
            safety_score
        FROM vetted_jobs
        WHERE
            is_active = TRUE
            AND (
                village  = %s
                OR block = %s
                OR district = %s
                OR job_title  ILIKE %s
                OR category   ILIKE %s
                OR description ILIKE %s
            )
        ORDER BY
            (CASE
                WHEN village  = %s THEN 1
                WHEN block    = %s THEN 2
                WHEN district = %s THEN 3
                ELSE 4
            END) ASC,
            safety_score DESC,
            created_at DESC
        LIMIT 10;
    """

    try:
        conn = psycopg2.connect(DB_URL)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (
                village, block, district,                   # WHERE location
                search_term, search_term, search_term,      # WHERE skills
                village, block, district,                   # ORDER BY priority
            ))
            res = cur.fetchall()

            if not res:
                return (
                    f"Nomoskar! I couldn't find any verified jobs in "
                    f"{village} or {block} right now."
                )

            results = []
            for r in res:
                loc_parts = [p for p in [r["village"], r["gram_panchayat"], r["block"]] if p]
                results.append({
                    "job_title":   r["job_title"],
                    "sector":      r["category"],
                    "description": r["description"] or "N/A",
                    "pay":         f"₹{r['pay_rate_daily']} per day" if r["pay_rate_daily"] else "N/A",
                    "duration":    f"{r['duration_days']} days" if r["duration_days"] else "N/A",
                    "start_date":  str(r["start_date"]) if r["start_date"] else "Immediate",
                    "location":    ", ".join(loc_parts) or r["district"],
                    "verified_by": r["ngo_partner_name"] or "N/A",
                    "contact":     f"{r['contact_person']} ({r['contact_number']})" if r["contact_person"] else "N/A",
                    "safety_score": r["safety_score"],
                })

            return results

    except Exception as e:
        logger.error(f"❌ Vetted Jobs Tool Error: {e}")
        return "I'm having a little trouble looking at the job list right now. Please try again in a moment."
    finally:
        if "conn" in locals():
            conn.close()