"""
Configuration: thresholds, sector overrides, and industry mappings.
"""

# === Divergence thresholds (% difference from sector benchmark) ===
STRONG_DIVERGENCE_PCT = 30
MODERATE_DIVERGENCE_PCT = 15

# === Quality thresholds ===
MIN_ROE = 0.10              # 10%
MIN_CF_QUALITY = 0.8        # OCF / Net Income
MAX_DEBT_TO_EQUITY = 2.0    # D/E ratio (as a multiple, not %)

# === Absolute fallback thresholds (when no sector benchmark available) ===
ABSOLUTE_THRESHOLDS = {
    "forward_pe": {"cheap": 10.0, "expensive": 30.0},
    "ev_ebitda": {"cheap": 6.0, "expensive": 20.0},
    "fcf_yield": {"cheap": 0.08, "expensive": 0.02},  # Inverted: high = cheap
}

# === Cache settings ===
CACHE_EXPIRY_HOURS = 12
BENCHMARK_CACHE_DAYS = 30

# === Metric definitions ===
# direction: "lower" means lower value = cheaper/better
#             "higher" means higher value = cheaper/better
METRICS = {
    "forward_pe":  {"label": "Forward P/E",  "category": "cheapness", "direction": "lower",  "format": ".1f", "suffix": "x"},
    "ev_ebitda":   {"label": "EV/EBITDA",    "category": "cheapness", "direction": "lower",  "format": ".1f", "suffix": "x"},
    "fcf_yield":   {"label": "FCF Yield",    "category": "cheapness", "direction": "higher", "format": ".1%", "suffix": ""},
    "roe":         {"label": "ROE",          "category": "quality",   "direction": "higher", "format": ".1%", "suffix": ""},
    "debt_equity": {"label": "D/E Ratio",    "category": "health",    "direction": "lower",  "format": ".1f", "suffix": "x"},
    "cf_quality":  {"label": "CF Quality",   "category": "quality",   "direction": "higher", "format": ".1f", "suffix": "x"},
}

CHEAPNESS_METRICS = ["forward_pe", "ev_ebitda", "fcf_yield"]

# === Sector-specific overrides ===
SECTOR_OVERRIDES = {
    "Technology": {
        "suppress": ["price_to_book"],
        "note": "Tech companies often trade at high P/E; focus on PEG and EV/Revenue for growth names.",
    },
    "Financial Services": {
        "suppress": ["ev_ebitda"],
        "de_threshold": None,  # Disable D/E check — banks are structurally leveraged
        "note": "Banks operate at 8-20x leverage by design; D/E threshold does not apply. EV/EBITDA suppressed.",
    },
    "Energy": {
        "cyclicality_warning": True,
        "note": "Cyclical sector: P/E unreliable at earnings peaks/troughs. EV/EBITDA weighted more heavily.",
    },
    "Basic Materials": {
        "cyclicality_warning": True,
        "note": "Cyclical sector: current multiples may reflect peak/trough earnings, not normalized value.",
    },
    "Real Estate": {
        "suppress": ["forward_pe"],
        "note": "REITs valued on P/FFO, not P/E. Forward P/E suppressed.",
    },
}

# === yfinance industry → Damodaran industry mapping ===
# Damodaran uses ~150 granular names; yfinance uses Yahoo's taxonomy.
# This maps the most common ones. Unmapped industries fall back to broad sector averages.
INDUSTRY_MAP = {
    # Technology
    "Software—Application": "Software (System & Application)",
    "Software—Infrastructure": "Software (System & Application)",
    "Software - Application": "Software (System & Application)",
    "Software - Infrastructure": "Software (System & Application)",
    "Semiconductors": "Semiconductor",
    "Semiconductor Equipment & Materials": "Semiconductor Equip",
    "Internet Content & Information": "Software (Internet)",
    "Consumer Electronics": "Electronics (Consumer & Office)",
    "Electronic Components": "Electronics (Consumer & Office)",
    "Information Technology Services": "Information Services",
    "Communication Equipment": "Telecom. Equipment",
    # Financials
    "Banks—Diversified": "Bank (Money Center)",
    "Banks—Regional": "Banks (Regional)",
    "Banks - Diversified": "Bank (Money Center)",
    "Banks - Regional": "Banks (Regional)",
    "Insurance—Diversified": "Insurance (General)",
    "Insurance—Life": "Insurance (Life)",
    "Insurance—Property & Casualty": "Insurance (Prop/Cas.)",
    "Insurance - Diversified": "Insurance (General)",
    "Capital Markets": "Brokerage & Investment Banking",
    "Asset Management": "Brokerage & Investment Banking",
    "Financial Data & Stock Exchanges": "Information Services",
    # Healthcare
    "Drug Manufacturers—General": "Drugs (Pharmaceutical)",
    "Drug Manufacturers—Specialty & Generic": "Drugs (Pharmaceutical)",
    "Drug Manufacturers - General": "Drugs (Pharmaceutical)",
    "Biotechnology": "Drugs (Biotechnology)",
    "Medical Devices": "Healthcare Products",
    "Health Care Plans": "Healthcare Support Services",
    "Diagnostics & Research": "Healthcare Products",
    "Medical Instruments & Supplies": "Healthcare Products",
    # Energy
    "Oil & Gas Integrated": "Oil/Gas (Integrated)",
    "Oil & Gas E&P": "Oil/Gas (Production and Exploration)",
    "Oil & Gas Midstream": "Oil/Gas Distribution",
    "Oil & Gas Equipment & Services": "Oilfield Svcs/Equip.",
    # Industrials
    "Aerospace & Defense": "Aerospace/Defense",
    "Railroads": "Transportation (Railroads)",
    "Airlines": "Air Transport",
    "Trucking": "Trucking",
    "Industrial Distribution": "Diversified",
    "Specialty Industrial Machinery": "Machinery",
    "Farm & Heavy Construction Machinery": "Machinery",
    # Consumer
    "Auto Manufacturers": "Auto & Truck",
    "Auto Parts": "Auto Parts",
    "Restaurants": "Restaurant/Dining",
    "Retail—Apparel & Specialty": "Retail (Special Lines)",
    "Internet Retail": "Retail (Online)",
    "Discount Stores": "Retail (General)",
    "Home Improvement Retail": "Retail (Building Supply)",
    "Grocery Stores": "Retail (Grocery and Food)",
    "Beverages—Non-Alcoholic": "Beverage (Soft)",
    "Beverages—Alcoholic": "Beverage (Alcoholic)",
    "Household & Personal Products": "Household Products",
    "Packaged Foods": "Food Processing",
    "Tobacco": "Tobacco",
    # Communication Services
    "Telecom Services": "Telecom Services",
    "Entertainment": "Entertainment",
    "Electronic Gaming & Multimedia": "Entertainment",
    "Advertising Agencies": "Advertising",
    "Broadcasting": "Broadcasting",
    "Publishing": "Publishing & Newspapers",
    # Utilities
    "Utilities—Regulated Electric": "Utility (General)",
    "Utilities—Diversified": "Utility (General)",
    "Utilities—Renewable": "Power",
    "Utilities - Regulated Electric": "Utility (General)",
    # Real Estate
    "REIT—Diversified": "REIT",
    "REIT—Residential": "REIT",
    "REIT—Industrial": "REIT",
    "REIT—Retail": "REIT",
    "REIT—Office": "REIT",
    "REIT—Healthcare Facilities": "REIT",
    "REIT - Diversified": "REIT",
    # Materials
    "Gold": "Metals & Mining",
    "Steel": "Steel",
    "Copper": "Metals & Mining",
    "Chemicals": "Chemical (Basic)",
    "Specialty Chemicals": "Chemical (Specialty)",
    "Building Materials": "Building Materials",
}

# === Broad sector fallback benchmarks ===
# Used when the specific Damodaran industry can't be matched.
# Values are approximate US medians — updated manually from Damodaran January 2026 data.
SECTOR_FALLBACK = {
    "Technology":              {"pe": 30.0, "pb": 7.0,  "ev_ebitda": 22.0},
    "Healthcare":              {"pe": 24.0, "pb": 4.0,  "ev_ebitda": 16.0},
    "Financial Services":      {"pe": 13.0, "pb": 1.4,  "ev_ebitda": None},
    "Energy":                  {"pe": 11.0, "pb": 1.6,  "ev_ebitda": 6.0},
    "Consumer Cyclical":       {"pe": 20.0, "pb": 3.5,  "ev_ebitda": 13.0},
    "Consumer Defensive":      {"pe": 21.0, "pb": 4.0,  "ev_ebitda": 15.0},
    "Industrials":             {"pe": 22.0, "pb": 4.0,  "ev_ebitda": 14.0},
    "Basic Materials":         {"pe": 14.0, "pb": 2.0,  "ev_ebitda": 8.0},
    "Communication Services":  {"pe": 18.0, "pb": 3.5,  "ev_ebitda": 12.0},
    "Real Estate":             {"pe": 35.0, "pb": 2.0,  "ev_ebitda": 18.0},
    "Utilities":               {"pe": 18.0, "pb": 1.8,  "ev_ebitda": 12.0},
}
