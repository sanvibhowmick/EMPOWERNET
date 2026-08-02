# app/tools/jobs.py

import logging
from sqlalchemy import text
from langchain_core.tools import tool

from app.core.db import engine

logger = logging.getLogger(__name__)

# FIX (weak point #4): the README claims "jobs.py filters out sites with
# safety_score < 2.0 from all future job searches," but the query previously
# only used safety_score in ORDER BY, never in WHERE -- unsafe sites were
# still returned, just ranked lower. We now filter them out for real. To
# avoid silently showing nothing in a village where every listed site has
# been flagged unsafe, we run the safe-only query first and only fall back
# to the unfiltered (but still safety-ranked) query -- with an explicit
# warning in the response -- if the safe query returns zero rows.
SAFETY_SCORE_THRESHOLD = 2.0

_BASE_QUERY = """
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
        {safety_clause}
        AND (
            village  = :village
            OR block = :block
            OR district = :district
            OR job_title  ILIKE :search_term
            OR category   ILIKE :search_term
            OR description ILIKE :search_term
        )
    ORDER BY
        (CASE
            WHEN village  = :village THEN 1
            WHEN block    = :block THEN 2
            WHEN district = :district THEN 3
            ELSE 4
        END) ASC,
        safety_score DESC,
        created_at DESC
    LIMIT 10;
"""


def _rows_to_results(res):
    results = []
    for r in res:
        loc_parts = [p for p in [r.village, r.gram_panchayat, r.block] if p]
        results.append({
            "job_title":    r.job_title,
            "sector":       r.category,
            "description":  r.description or "N/A",
            "pay":          f"₹{r.pay_rate_daily} per day" if r.pay_rate_daily else "N/A",
            "duration":     f"{r.duration_days} days" if r.duration_days else "N/A",
            "start_date":   str(r.start_date) if r.start_date else "Immediate",
            "location":     ", ".join(loc_parts) or r.district,
            "verified_by":  r.ngo_partner_name or "N/A",
            "contact":      f"{r.contact_person} ({r.contact_number})" if r.contact_person else "N/A",
            "safety_score": r.safety_score,
        })
    return results


@tool("match_local_jobs")
def match_local_jobs(skills: str, district: str, block: str, village: str):
    """
    Finds verified job openings for unorganised sector workers.
    Priority 1: Exact village match.
    Priority 2: Same block.
    Priority 3: Same district or skill keyword match.
    Only returns active jobs with an acceptable safety score; sites flagged
    unsafe by community hazard reports (safety_score below 2.0) are excluded
    from results whenever a safe alternative exists.
    """
    search_term = f"%{skills}%" if skills and str(skills).lower() != "none" else "%"
    params = {
        "village": village, "block": block, "district": district,
        "search_term": search_term,
    }

    try:
        with engine.connect() as conn:
            # 1. Try the safety-filtered query first (matches README's stated behavior).
            safe_query = text(_BASE_QUERY.format(safety_clause="AND safety_score >= :threshold"))
            res = conn.execute(safe_query, {**params, "threshold": SAFETY_SCORE_THRESHOLD}).fetchall()

            warning = ""
            if not res:
                # 2. No safe listings found -- fall back to unfiltered results
                # (still ranked safety_score DESC) so the user isn't left with
                # nothing, but flag it explicitly rather than silently
                # showing unsafe sites as if they were vetted-safe.
                fallback_query = text(_BASE_QUERY.format(safety_clause=""))
                res = conn.execute(fallback_query, params).fetchall()
                if res:
                    warning = (
                        "⚠️ No jobs currently meet our minimum safety score in this area -- "
                        "showing all listings ranked by safety score; please ask about site "
                        "safety before accepting work."
                    )

            if not res:
                return (
                    f"Nomoskar! I couldn't find any verified jobs in "
                    f"{village} or {block} right now."
                )

            results = _rows_to_results(res)
            if warning:
                return {"warning": warning, "jobs": results}
            return results

    except Exception as e:
        logger.error(f"❌ Vetted Jobs Tool Error: {e}")
        return "I'm having a little trouble looking at the job list right now. Please try again in a moment."
