import os
import time
import re
import requests
import urllib3
import psycopg2
from bs4 import BeautifulSoup
from urllib.parse import quote
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# --- INITIALIZATION ---
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_URL = os.getenv("DATABASE_URL")
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

BASE_URL = "https://nrlm.gov.in/shgOuterReports.do"
START_URL = f"{BASE_URL}?methodName=showDistrictPage&encd=32&stateName=WEST%20BENGAL"

# --- TEST LIMITS ---
MAX_BLOCKS = 5
MAX_GPS = 3
MAX_VILLAGES = 3
MAX_SHGS = 50


def get_soup(url):
    for _ in range(3):
        try:
            response = session.get(url, timeout=30, verify=False)
            if response.status_code == 200:
                return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"⚠️ Connection error: {e}")
            time.sleep(2)
    return None


def extract_js_params(col):
    a_tag = col.find("a")
    if not a_tag or not a_tag.get("href"):
        return None, None

    params = re.findall(r"'(.*?)'", a_tag["href"])
    if not params:
        return None, None

    entity_id = params[0]

    # Always use anchor visible text as the name — params[1] is unreliable
    # at village level it returns 'wb' (srtnm) instead of the actual village name
    entity_name = a_tag.get_text(strip=True)

    # Fallback to params[1] only if anchor text is empty
    if not entity_name and len(params) >= 2:
        entity_name = params[1]

    return entity_id, entity_name


def find_data_table(soup):
    if not soup:
        return None
    tables = soup.find_all("table")
    if not tables:
        return None
    return max(tables, key=lambda t: len(t.find_all("tr")))


def scrape_nrlm():
    if not DB_URL:
        print("❌ DATABASE_URL missing")
        return

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    print("🚀 Starting EmpowerNet Scraper (TEST MODE)...")
    print(f"🔬 Limits: {MAX_BLOCKS} blocks | {MAX_GPS} GPs | {MAX_VILLAGES} villages | {MAX_SHGS} SHGs\n")

    soup = get_soup(START_URL)
    dist_table = find_data_table(soup)
    if not dist_table:
        print("❌ Could not find district table.")
        return

    for row in dist_table.find_all("tr"):
        cols = row.find_all("td")
        if not cols:
            continue

        dist_id, dist_name = extract_js_params(cols[1])
        if not dist_id or not dist_name or "total" in dist_name.lower():
            continue

        print(f"\n📍 District: {dist_name}")

        block_url = (
            f"{BASE_URL}?methodName=showBlockPage"
            f"&encd={dist_id}"
            f"&stateName=WEST%20BENGAL"
            f"&districtName={quote(dist_name)}"
        )
        block_table = find_data_table(get_soup(block_url))
        if not block_table:
            continue

        block_count = 0
        for b_row in block_table.find_all("tr"):
            if block_count >= MAX_BLOCKS:
                print(f"  ⏹ Block limit ({MAX_BLOCKS}) reached, moving to next district.")
                break

            b_cols = b_row.find_all("td")
            if not b_cols:
                continue

            block_id, block_name = extract_js_params(b_cols[1])
            if not block_id or not block_name or "total" in block_name.lower():
                continue

            block_count += 1
            print(f"  ∟ Block [{block_count}/{MAX_BLOCKS}]: {block_name}")

            gp_url = (
                f"{BASE_URL}?methodName=showGPPage"
                f"&encd={block_id}"
                f"&stateName=WEST%20BENGAL"
                f"&districtName={quote(dist_name)}"
                f"&blockName={quote(block_name)}"
            )
            gp_table = find_data_table(get_soup(gp_url))
            if not gp_table:
                continue

            gp_count = 0
            for gp_row in gp_table.find_all("tr"):
                if gp_count >= MAX_GPS:
                    print(f"    ⏹ GP limit ({MAX_GPS}) reached, moving to next block.")
                    break

                gp_cols = gp_row.find_all("td")
                if not gp_cols:
                    continue

                gp_id, gp_name = extract_js_params(gp_cols[1])
                if not gp_id or not gp_name or "total" in gp_name.lower():
                    continue

                gp_count += 1
                print(f"    ∟ GP [{gp_count}/{MAX_GPS}]: {gp_name}")

                v_url = (
                    f"{BASE_URL}?methodName=showVillagePage"
                    f"&encd={gp_id}"
                    f"&stateName=WEST%20BENGAL"
                    f"&districtName={quote(dist_name)}"
                    f"&blockName={quote(block_name)}"
                    f"&grampanchayatName={quote(gp_name)}"
                )
                v_table = find_data_table(get_soup(v_url))
                if not v_table:
                    continue

                village_count = 0
                for v_row in v_table.find_all("tr"):
                    if village_count >= MAX_VILLAGES:
                        print(f"      ⏹ Village limit ({MAX_VILLAGES}) reached, moving to next GP.")
                        break

                    v_cols = v_row.find_all("td")
                    if not v_cols:
                        continue

                    v_id, v_name = extract_js_params(v_cols[1])
                    if not v_id or not v_name or "total" in v_name.lower():
                        continue

                    village_count += 1
                    print(f"      ∟ Village [{village_count}/{MAX_VILLAGES}]: {v_name}")

                    cur.execute("""
                        INSERT INTO administrative_hierarchy (district, block, gram_panchayat, village)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (dist_name, block_name, gp_name, v_name))

                    shg_url = (
                        f"{BASE_URL}?methodName=showSHGPage"
                        f"&encd={v_id}"
                        f"&srtnm=wb"
                        f"&stateName=WEST%20BENGAL"
                        f"&districtName={quote(dist_name)}"
                        f"&blockName={quote(block_name)}"
                        f"&grampanchayatName={quote(gp_name)}"
                        f"&villageName={quote(v_name)}"
                    )
                    shg_table = find_data_table(get_soup(shg_url))

                    if shg_table:
                        shg_batch = []
                        for s_row in shg_table.find_all("tr"):
                            if len(shg_batch) >= MAX_SHGS:
                                print(f"        ⏹ SHG limit ({MAX_SHGS}) reached for {v_name}.")
                                break

                            s_cols = s_row.find_all("td")
                            if len(s_cols) < 5 or not s_cols[0].text.strip().isdigit():
                                continue

                            shg_id, _ = extract_js_params(s_cols[1])
                            shg_name = s_cols[1].text.strip()

                            if not shg_id:
                                shg_id = f"{v_id}_{s_cols[0].text.strip()}"

                            shg_batch.append((
                                shg_name,
                                "",
                                dist_name,
                                block_name,
                                gp_name,
                                v_name,
                                shg_id,
                                "General"
                            ))

                        if shg_batch:
                            execute_values(cur, """
                                INSERT INTO self_help_groups
                                    (shg_name, leader_name, district, block, gram_panchayat, village, nrlm_shg_id, category)
                                VALUES %s
                                ON CONFLICT (nrlm_shg_id) DO UPDATE
                                    SET shg_name = EXCLUDED.shg_name;
                            """, shg_batch)
                            conn.commit()
                            print(f"        ✅ Saved {len(shg_batch)} SHGs in {v_name}")

                    time.sleep(0.4)

    cur.close()
    conn.close()
    print("\n✨ Test Run Complete!")


# ✅ ENTRY POINT
if __name__ == "__main__":
    scrape_nrlm()