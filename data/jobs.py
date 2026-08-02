# generate_mock_jobs.py

import random
from faker import Faker
from sqlalchemy import text
from app.core.db import engine
# FIX (weak point #11): previously this file hardcoded its own
# WB_GEOGRAPHY dict with district names like "MEDINIPUR EAST", "MALDAH",
# "DINAJPUR UTTAR", "COOCHBEHAR", "DARJEELING GTA" -- different spellings
# from app/api/dashboard.py's canonical district list ("PURBA MEDINIPUR",
# "MALDA", "UTTAR DINAJPUR", "COOCH BEHAR", "DARJEELING"). Since every join
# in this schema is a plain string-equality match (no foreign keys), that
# meant every job seeded by this script silently failed to show up on the
# dashboard's choropleth map. Now both import the same names from
# app/core/districts.py.
from app.core.districts import SAMPLE_BLOCKS

fake = Faker('en_IN')

# Sector and Job logic remains consistent for rural focus
CATEGORIES = {
    "Agriculture": ["Paddy Harvester", "Jute Processor", "Irrigation Technician"],
    "Construction": ["Assistant Mason", "Brick Layer", "Concrete Mixer Operator"],
    "Handicraft": ["Zari Embroiderer", "Handloom Weaver", "Clay Modeller"],
    "Services": ["Domestic Help", "Community Cook", "Local Delivery Runner"],
    "Technical": ["Tube-well Repairer", "Cycle Mechanic", "Solar Lamp Tech"]
}

NGO_PARTNERS = ["Bangla Rural Upliftment", "Women Empowerment Cell", "BuildLocal NGO", "Paschim Banga Vikas"]

def generate_statewide_jobs(count=1000):
    jobs_batch = []

    for _ in range(count):
        # 1. Select dynamic location (canonical district/block names)
        district = random.choice(list(SAMPLE_BLOCKS.keys()))
        block = random.choice(SAMPLE_BLOCKS[district])
        village = f"{block}_VILLAGE_{random.randint(1, 5)}"

        # 2. Select job details
        category = random.choice(list(CATEGORIES.keys()))
        job_title = random.choice(CATEGORIES[category])
        pay = random.randint(350, 850)

        jobs_batch.append({
            "job_title": job_title,
            "description": f"Looking for {job_title} in {village}.",
            "category": category,
            "pay_rate_daily": pay,
            "duration_days": random.randint(3, 60),
            "district": district,
            "block": block,
            "gram_panchayat": f"{block}_GP",
            "village": village,
            "ngo_partner_name": random.choice(NGO_PARTNERS),
            "contact_person": fake.name(),
            "contact_number": fake.phone_number(),
            # FIX (weak point #4, seed-data side): give seeded jobs a
            # realistic starting safety_score so match_local_jobs' new
            # `safety_score >= 2.0` filter (see app/tools/jobs.py) has
            # something meaningful to filter on, instead of relying on the
            # column default (previously irrelevant, since nothing filtered
            # on it).
            "safety_score": round(random.uniform(1.0, 5.0), 1),
        })
    return jobs_batch

def insert_to_db():
    data = generate_statewide_jobs(1000)

    with engine.begin() as conn:
        # Clear old data for a clean statewide test
        conn.execute(text("TRUNCATE TABLE vetted_jobs;"))

        conn.execute(
            text("""
                INSERT INTO vetted_jobs (
                    job_title, description, category, pay_rate_daily, duration_days,
                    district, block, gram_panchayat, village, ngo_partner_name,
                    contact_person, contact_number, safety_score, is_active
                ) VALUES (
                    :job_title, :description, :category, :pay_rate_daily, :duration_days,
                    :district, :block, :gram_panchayat, :village, :ngo_partner_name,
                    :contact_person, :contact_number, :safety_score, TRUE
                );
            """),
            data,
        )

    print(f"🚀 Inserted {len(data)} jobs across all 23 districts.")

if __name__ == "__main__":
    insert_to_db()
