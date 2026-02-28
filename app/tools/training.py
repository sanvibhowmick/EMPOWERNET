# app/tools/training.py

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

@tool("match_training_programs")
def get_training_programs(category: str, district: str, block: str, village: str):
    """
    Finds vocational training and skill-building programs for unorganised sector workers.
    Matches by district first, then falls back to category keywords.
    """

    search_term = f"%{category}%" if category and str(category).lower() != "none" else "%"

    # training_programs table has: district, location_details (no village/block columns)
    # We use district for location matching and category/course_name for keyword matching.
    query = """
        SELECT
            course_name,
            agency_name,
            category,
            skill_level,
            duration_hours,
            enrollment_deadline,
            course_fee,
            stipend_provided,
            certification_type,
            min_wage_guarantee,
            district,
            location_details,
            source_url
        FROM training_programs
        WHERE (
            district ILIKE %s
            OR course_name ILIKE %s
            OR category ILIKE %s
        )
        ORDER BY
            (CASE
                WHEN district ILIKE %s THEN 1
                ELSE 2
            END) ASC,
            enrollment_deadline ASC NULLS LAST
        LIMIT 5;
    """

    try:
        conn = psycopg2.connect(DB_URL)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            dist_term = f"%{district}%" if district else "%"
            cur.execute(query, (
                dist_term, search_term, search_term,   # WHERE
                dist_term,                             # ORDER BY
            ))
            res = cur.fetchall()

            if not res:
                return (
                    f"Nomoskar! I couldn't find any training courses in {district} "
                    f"for '{category}' yet. Try broadening the category."
                )

            results = []
            for r in res:
                fee = r["course_fee"] or 0
                fee_text = "Free" if float(fee) == 0 else f"₹{fee}"
                stipend_text = " (includes stipend)" if r["stipend_provided"] else ""
                wage = f" | Target wage: ₹{r['min_wage_guarantee']}/day" if r["min_wage_guarantee"] else ""

                results.append({
                    "course":       r["course_name"],
                    "provider":     r["agency_name"],
                    "category":     r["category"],
                    "level":        r["skill_level"],
                    "duration":     f"{r['duration_hours']} hours" if r["duration_hours"] else "N/A",
                    "fee":          f"{fee_text}{stipend_text}",
                    "deadline":     str(r["enrollment_deadline"]) if r["enrollment_deadline"] else "Open",
                    "certificate":  r["certification_type"],
                    "location":     r["location_details"] or r["district"],
                    "after_training": wage.strip(" | ") or "N/A",
                    "source":       r["source_url"],
                })

            return results

    except Exception as e:
        logger.error(f"❌ Training Tool Error: {e}")
        return "I'm having a little trouble looking up the training list right now. Please try again in a bit."
    finally:
        if "conn" in locals():
            conn.close()