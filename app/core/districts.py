# app/core/districts.py
"""
Single source of truth for West Bengal district names and their approximate
centroid coordinates.

FIXES weak point #11: data/jobs.py and data/train.py previously hardcoded
their own district-name lists (e.g. "MEDINIPUR EAST", "MALDAH",
"DINAJPUR UTTAR", "COOCHBEHAR", "DARJEELING GTA", "24 PARGANAS NORTH"), while
app/api/dashboard.py hardcoded a *different* set of official names for the
same 23 districts (e.g. "PURBA MEDINIPUR", "MALDA", "UTTAR DINAJPUR",
"COOCH BEHAR", "DARJEELING", "NORTH 24 PARGANAS"). Because every join between
these tables is a plain string-equality match (no foreign keys — see
Section 5.2/5.3 of the interview-prep doc), the mismatch silently orphaned
every mock job/training row from the dashboard's choropleth map.

Every script that needs a district name (mock-data generators, the dashboard,
any future seed/ETL script) should import from here instead of typing its own
list. If a name ever needs to change, it changes in exactly one place.
"""

# Canonical (official) district names, matching what app/api/dashboard.py's
# choropleth/geo layer expects, and what should be written into
# administrative_hierarchy.district / vetted_jobs.district / etc.
DISTRICT_CENTROIDS = {
    "KOLKATA": (22.57, 88.36),
    "HOWRAH": (22.59, 88.10),
    "HOOGHLY": (22.90, 87.90),
    "NORTH 24 PARGANAS": (22.99, 88.68),
    "SOUTH 24 PARGANAS": (22.05, 88.60),
    "NADIA": (23.47, 88.52),
    "MURSHIDABAD": (24.18, 88.27),
    "BIRBHUM": (23.90, 87.70),
    "PURBA BARDHAMAN": (23.23, 87.86),
    "PASCHIM BARDHAMAN": (23.50, 87.25),
    "BANKURA": (23.23, 87.07),
    "PURULIA": (23.33, 86.36),
    "JHARGRAM": (22.45, 86.53),
    "PASCHIM MEDINIPUR": (22.42, 87.32),
    "PURBA MEDINIPUR": (22.08, 87.68),
    "MALDA": (25.00, 88.13),
    "UTTAR DINAJPUR": (25.75, 88.05),
    "DAKSHIN DINAJPUR": (25.35, 88.43),
    "JALPAIGURI": (26.55, 88.72),
    "DARJEELING": (27.03, 88.26),
    "KALIMPONG": (27.07, 88.65),
    "ALIPURDUAR": (26.48, 89.43),
    "COOCH BEHAR": (26.32, 89.45),
}

ALL_DISTRICTS = list(DISTRICT_CENTROIDS.keys())

# Sample blocks per district, used only by the mock-data generators
# (data/jobs.py, data/train.py) to seed plausible test rows. Real block
# names for production come from the `administrative_hierarchy` table via
# app/tools/spatial.py — this dict exists purely so mock data seeds against
# the *same* district keys the rest of the app uses.
SAMPLE_BLOCKS = {
    "NORTH 24 PARGANAS": ["AMDANGA", "BARASAT", "DEGANGA", "HABRA", "RAJARHAT"],
    "SOUTH 24 PARGANAS": ["BARUIPUR", "CANNING", "SONARPUR", "DIAMOND HARBOUR"],
    "NADIA": ["KRISHNANAGAR", "RANAGHAT", "CHAKDAHA", "TEHATTA", "HANSKHALI"],
    "HOWRAH": ["ULUBERIA", "AMTA", "BAGNAN", "DOMJUR", "SANKRAIL"],
    "HOOGHLY": ["CHINSURAH", "SERAMPORE", "ARAMBAGH", "PANDUA"],
    "BANKURA": ["BISHNUPUR", "KHATRA", "SALTORA", "MEJIA"],
    "BIRBHUM": ["SURI", "BOLPUR", "RAMPURHAT", "SAINTHIA"],
    "PURBA BARDHAMAN": ["BURDWAN", "KALNA", "KATWA", "MEMARI"],
    "PASCHIM BARDHAMAN": ["ASANSOL", "DURGAPUR", "RANIGANJ"],
    "PURULIA": ["RAGHUNATHPUR", "JHALDA", "BAGHMUNDI"],
    "PURBA MEDINIPUR": ["TAMLUK", "HALDIA", "CONTAI", "EGRA"],
    "PASCHIM MEDINIPUR": ["MIDNAPORE", "KHARAGPUR", "GHATAL"],
    "JHARGRAM": ["BINPUR", "NAYAGRAM", "GOPIBALLAVPUR"],
    "MURSHIDABAD": ["BERHAMPORE", "DOMKAL", "KANDI", "JANGIPUR"],
    "MALDA": ["ENGLISH BAZAR", "CHANCHAL", "GAZOLE"],
    "UTTAR DINAJPUR": ["RAIGANJ", "ISLAMPUR", "DALKHOLA"],
    "DAKSHIN DINAJPUR": ["BALURGHAT", "GANGARAMPUR"],
    "JALPAIGURI": ["MALBAZAR", "DHUPGURI", "MAINAGURI"],
    "ALIPURDUAR": ["FALAKATA", "KALCHINI", "MADARIHAT"],
    "COOCH BEHAR": ["DINHATA", "MEKLIGANJ", "TUFANGANJ"],
    "DARJEELING": ["KURSEONG", "MIRIK", "SILIGURI"],
    "KALIMPONG": ["GORUBATHAN", "LAVA"],
    "KOLKATA": ["CENTRAL", "NORTH", "SOUTH", "EAST"],
}
