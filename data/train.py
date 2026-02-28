import os
import random
import psycopg2
from faker import Faker
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
fake = Faker('en_IN')

# --- WB GEOGRAPHY & UNORGANIZED SECTORS ---
# Using the standard 23-district keys for cross-node compatibility
DISTRICTS = [
    "24 PARGANAS NORTH", "24 PARGANAS SOUTH", "NADIA", "HOWRAH", "HOOGHLY", 
    "BANKURA", "BIRBHUM", "PURBA BARDHAMAN", "PASCHIM BARDHAMAN", "PURULIA", 
    "MEDINIPUR EAST", "MEDINIPUR WEST", "JHARGRAM", "MURSHIDABAD", "MALDAH", 
    "DINAJPUR UTTAR", "DINAJPUR DAKSHIN", "JALPAIGURI", "ALIPURDUAR", 
    "COOCHBEHAR", "DARJEELING GTA", "KALIMPONG", "KOLKATA"
]

TRAINING_COURSES = {
    "Handicraft": ["Zari Embroidery", "Kantha Stitching", "Bamboo Crafting", "Jute Weaving"],
    "Agriculture": ["Organic Farming", "Mushroom Cultivation", "Seed Banking"],
    "Technical": ["Solar Pump Repair", "Mobile Servicing", "Basic Electricals"],
    "Community": ["SHG Management", "Mid-day Meal Cooking", "Community Health Support"]
}

SKILL_LEVELS = ["Unskilled", "Semi-Skilled", "Skilled"]
CERTIFIERS = ["PBSSD", "NCVT", "NGO Certified", "Local Industry Board"]

def generate_mock_training_rows(count=200) -> list[tuple]:
    """Generates synthetic training data tailored for West Bengal workers."""
    rows = []
    for _ in range(count):
        category = random.choice(list(TRAINING_COURSES.keys()))
        course_name = random.choice(TRAINING_COURSES[category])
        district = random.choice(DISTRICTS)
        
        rows.append((
            f"{course_name} Training",             # course_name
            f"{district} Vocational Center",       # agency_name
            category,                              # category
            random.choice(SKILL_LEVELS),           # skill_level
            random.randint(40, 200),               # duration_hours
            fake.future_date(end_date="+30d"),     # enrollment_deadline
            0.0 if random.random() > 0.3 else 500, # course_fee (mostly free)
            random.choice([True, False]),          # stipend_provided
            random.choice(CERTIFIERS),             # certification_type
            399.0 if district in ["KOLKATA", "HOWRAH"] else 375.0, # min_wage_guarantee (2026 rates)
            district,                              # district
            f"{fake.street_name()}, {fake.city()}",# location_details
            "https://empowernet.org/mock-data"     # source_url
        ))
    return rows

def insert_rows(rows: list[tuple]):
    """Standard upsert into the training_programs table."""
    if not rows or not DB_URL:
        print("❌ Missing rows or DATABASE_URL.")
        return

    try:
        conn = psycopg2.connect(DB_URL)
        with conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO training_programs (
                        course_name, agency_name, category, skill_level,
                        duration_hours, enrollment_deadline, course_fee,
                        stipend_provided, certification_type, min_wage_guarantee,
                        district, location_details, source_url
                    )
                    VALUES %s
                    ON CONFLICT DO NOTHING;
                    """,
                    rows
                )
        print(f"✅ Successfully inserted {len(rows)} mock training programs.")
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    # GENERATE AND INSERT MOCK DATA
    mock_data = generate_mock_training_rows(200)
    insert_rows(mock_data)