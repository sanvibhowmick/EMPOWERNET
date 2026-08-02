import random
from faker import Faker
from sqlalchemy import text
from app.core.db import engine
# FIX (weak point #11): DISTRICTS used to be a second, independently typed
# copy of the mismatched district-name list (shared with the old
# data/jobs.py) -- now sourced from the same single canonical list as
# app/api/dashboard.py and data/jobs.py.
from app.core.districts import ALL_DISTRICTS as DISTRICTS

fake = Faker('en_IN')

TRAINING_COURSES = {
    "Handicraft": ["Zari Embroidery", "Kantha Stitching", "Bamboo Crafting", "Jute Weaving"],
    "Agriculture": ["Organic Farming", "Mushroom Cultivation", "Seed Banking"],
    "Technical": ["Solar Pump Repair", "Mobile Servicing", "Basic Electricals"],
    "Community": ["SHG Management", "Mid-day Meal Cooking", "Community Health Support"]
}

SKILL_LEVELS = ["Unskilled", "Semi-Skilled", "Skilled"]
CERTIFIERS = ["PBSSD", "NCVT", "NGO Certified", "Local Industry Board"]

def generate_mock_training_rows(count=200) -> list[dict]:
    """Generates synthetic training data tailored for West Bengal workers."""
    rows = []
    for _ in range(count):
        category = random.choice(list(TRAINING_COURSES.keys()))
        course_name = random.choice(TRAINING_COURSES[category])
        district = random.choice(DISTRICTS)

        rows.append({
            "course_name": f"{course_name} Training",
            "agency_name": f"{district} Vocational Center",
            "category": category,
            "skill_level": random.choice(SKILL_LEVELS),
            "duration_hours": random.randint(40, 200),
            "enrollment_deadline": fake.future_date(end_date="+30d"),
            "course_fee": 0.0 if random.random() > 0.3 else 500,
            "stipend_provided": random.choice([True, False]),
            "certification_type": random.choice(CERTIFIERS),
            "min_wage_guarantee": 399.0 if district in ["KOLKATA", "HOWRAH"] else 375.0,
            "district": district,
            "location_details": f"{fake.street_name()}, {fake.city()}",
            "source_url": "https://empowernet.org/mock-data",
        })
    return rows

def insert_rows(rows: list[dict]):
    """Standard upsert into the training_programs table."""
    if not rows:
        print("❌ No rows to insert.")
        return

    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO training_programs (
                        course_name, agency_name, category, skill_level,
                        duration_hours, enrollment_deadline, course_fee,
                        stipend_provided, certification_type, min_wage_guarantee,
                        district, location_details, source_url
                    )
                    VALUES (
                        :course_name, :agency_name, :category, :skill_level,
                        :duration_hours, :enrollment_deadline, :course_fee,
                        :stipend_provided, :certification_type, :min_wage_guarantee,
                        :district, :location_details, :source_url
                    )
                    ON CONFLICT DO NOTHING;
                """),
                rows,
            )
        print(f"✅ Successfully inserted {len(rows)} mock training programs.")
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    mock_data = generate_mock_training_rows(200)
    insert_rows(mock_data)
