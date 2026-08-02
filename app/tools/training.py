# app/tools/training.py

import logging
from sqlalchemy import text
from langchain_core.tools import tool

from app.core.db import engine

logger = logging.getLogger(__name__)

@tool("match_training_programs")
def get_training_programs(category: str, district: str):
    """
    Finds vocational training and skill-building programs for unorganised sector workers.
    Matches by district first, then falls back to category keywords.
    """
    # FIX (weak point #5): this tool used to also accept `block` and
    # `village` parameters that were never referenced anywhere in the SQL --
    # training_programs has no block/village columns, so matching has always
    # been district-only. Keeping unused parameters in the signature implied
    # a granularity the tool doesn't actually support and was dead/misleading
    # code. opportunity_node has been updated to match this signature.

    search_term = f"%{category}%" if category and str(category).lower() != "none" else "%"
    dist_term = f"%{district}%" if district else "%"

    query = text("""
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
            district ILIKE :dist_term
            OR course_name ILIKE :search_term
            OR category ILIKE :search_term
        )
        ORDER BY
            (CASE
                WHEN district ILIKE :dist_term THEN 1
                ELSE 2
            END) ASC,
            enrollment_deadline ASC NULLS LAST
        LIMIT 5;
    """)

    try:
        with engine.connect() as conn:
            res = conn.execute(query, {"dist_term": dist_term, "search_term": search_term}).fetchall()

            if not res:
                return (
                    f"Nomoskar! I couldn't find any training courses in {district} "
                    f"for '{category}' yet. Try broadening the category."
                )

            results = []
            for r in res:
                fee = r.course_fee or 0
                fee_text = "Free" if float(fee) == 0 else f"₹{fee}"
                stipend_text = " (includes stipend)" if r.stipend_provided else ""
                wage = f" | Target wage: ₹{r.min_wage_guarantee}/day" if r.min_wage_guarantee else ""

                results.append({
                    "course":         r.course_name,
                    "provider":       r.agency_name,
                    "category":       r.category,
                    "level":          r.skill_level,
                    "duration":       f"{r.duration_hours} hours" if r.duration_hours else "N/A",
                    "fee":            f"{fee_text}{stipend_text}",
                    "deadline":       str(r.enrollment_deadline) if r.enrollment_deadline else "Open",
                    "certificate":    r.certification_type,
                    "location":       r.location_details or r.district,
                    "after_training": wage.strip(" | ") or "N/A",
                    "source":         r.source_url,
                })

            return results

    except Exception as e:
        logger.error(f"❌ Training Tool Error: {e}")
        return "I'm having a little trouble looking up the training list right now. Please try again in a bit."
