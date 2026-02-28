# generate_mock_jobs.py

import os
import random
from faker import Faker
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
fake = Faker('en_IN')

# --- STATEWIDE GEOGRAPHY SAMPLER ---
# Maps all 23 districts to sample blocks to ensure coverage
WB_GEOGRAPHY = {
    "24 PARGANAS NORTH": ["AMDANGA", "BARASAT", "DEGANGA", "HABRA", "RAJARHAT"],
    "24 PARGANAS SOUTH": ["BARUIPUR", "CANNING", "SONARPUR", "DIAMOND HARBOUR"],
    "NADIA": ["KRISHNANAGAR", "RANAGHAT", "CHAKDAHA", "TEHATTA", "HANSKHALI"],
    "HOWRAH": ["ULUBERIA", "AMTA", "BAGNAN", "DOMJUR", "SANKRAIL"],
    "HOOGHLY": ["CHINSURAH", "SERAMPORE", "ARAMBAGH", "PANDUA"],
    "BANKURA": ["BISHNUPUR", "KHATRA", "SALTORA", "MEJIA"],
    "BIRBHUM": ["SURI", "BOLPUR", "RAMPURHAT", "SAINTHIA"],
    "PURBA BARDHAMAN": ["BURDWAN", "KALNA", "KATWA", "MEMARI"],
    "PASCHIM BARDHAMAN": ["ASANSOL", "DURGAPUR", "RANIGANJ"],
    "PURULIA": ["RAGHUNATHPUR", "JHALDA", "BAGHMUNDI"],
    "MEDINIPUR EAST": ["TAMLUK", "HALDIA", "CONTAI", "EGRA"],
    "MEDINIPUR WEST": ["MIDNAPORE", "KHARAGPUR", "GHATAL"],
    "JHARGRAM": ["BINPUR", "NAYAGRAM", "GOPIBALLAVPUR"],
    "MURSHIDABAD": ["BERHAMPORE", "DOMKAL", "KANDI", "JANGIPUR"],
    "MALDAH": ["ENGLISH BAZAR", "CHANCHAL", "GAZOLE"],
    "DINAJPUR UTTAR": ["RAIGANJ", "ISLAMPUR", "DALKHOLA"],
    "DINAJPUR DAKSHIN": ["BALURGHAT", "GANGARAMPUR"],
    "JALPAIGURI": ["MALBAZAR", "DHUPGURI", "MAINAGURI"],
    "ALIPURDUAR": ["FALAKATA", "KALCHINI", "MADARIHAT"],
    "COOCHBEHAR": ["DINHATA", "MEKLIGANJ", "TUFANGANJ"],
    "DARJEELING GTA": ["KURSEONG", "MIRIK", "SILIGURI"],
    "KALIMPONG": ["GORUBATHAN", "LAVA"],
    "KOLKATA": ["CENTRAL", "NORTH", "SOUTH", "EAST"]
}

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
        # 1. Select dynamic location
        district = random.choice(list(WB_GEOGRAPHY.keys()))
        block = random.choice(WB_GEOGRAPHY[district])
        village = f"{block}_VILLAGE_{random.randint(1, 5)}"
        
        # 2. Select job details
        category = random.choice(list(CATEGORIES.keys()))
        job_title = random.choice(CATEGORIES[category])
        pay = random.randint(350, 850)
        
        jobs_batch.append((
            job_title,
            f"Looking for {job_title} in {village}.",
            category,
            pay,
            random.randint(3, 60),
            district,
            block,
            f"{block}_GP",
            village,
            random.choice(NGO_PARTNERS),
            fake.name(),
            fake.phone_number()
        ))
    return jobs_batch

def insert_to_db():
    if not DB_URL:
        print("❌ DATABASE_URL missing.")
        return

    # Increase count to 1000 for full state coverage testing
    data = generate_statewide_jobs(1000)
    
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    # Clear old data for a clean statewide test
    cur.execute("TRUNCATE TABLE vetted_jobs;")

    execute_values(cur, """
        INSERT INTO vetted_jobs (
            job_title, description, category, pay_rate_daily, duration_days, 
            district, block, gram_panchayat, village, ngo_partner_name, 
            contact_person, contact_number
        ) VALUES %s;
    """, data)

    print(f"🚀 Inserted {len(data)} jobs across all 23 districts.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    insert_to_db()