from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
internal = ROOT / "data" / "raw" / "internal"
internal.mkdir(parents=True, exist_ok=True)

tier_summary = pd.DataFrame([
    ["Unregulated", 2175, 7.0, 35, 40, 0.50, 0.28, 8.5],
    ["Tier 1", 964, 3.1, 38, 109, 0.52, 0.27, 3.3],
    ["Tier 2", 5329, 17.0, 40, 119, 0.53, 0.26, 16.8],
    ["Tier 3", 13314, 42.6, 42, 260, 0.54, 0.25, 96.5],
    ["Tier 4i", 5259, 16.8, 45, 341, 0.55, 0.24, 26.2],
    ["Tier 4f", 3498, 11.2, 48, 631, 0.56, 0.23, 38.4],
    ["Stage V", 716, 2.3, 50, 829, 0.58, 0.22, 14.1],
], columns=["tier","count","fleet_share_pct","power_kw","hours_per_year","load_factor","sfc_l_per_kwh","fuel_ml"])

cohort_rows = [
    ("Pre-1996", 1844, {"Unregulated": 1844}),
    ("1996-1999", 1103, {"Unregulated": 331, "Tier 1": 772}),
    ("2000-2005", 3850, {"Tier 1": 192, "Tier 2": 2888, "Tier 3": 770}),
    ("2006-2010", 3735, {"Tier 2": 1120, "Tier 3": 2428, "Tier 4i": 187}),
    ("2011-2013", 2893, {"Tier 2": 434, "Tier 3": 1736, "Tier 4i": 579, "Tier 4f": 145}),
    ("2014-2018", 7309, {"Tier 2": 585, "Tier 3": 4020, "Tier 4i": 1608, "Tier 4f": 950, "Stage V": 146}),
    ("2019-2020", 3037, {"Tier 2": 152, "Tier 3": 1367, "Tier 4i": 790, "Tier 4f": 607, "Stage V": 121}),
    ("2021-2025", 7482, {"Tier 2": 150, "Tier 3": 2993, "Tier 4i": 2095, "Tier 4f": 1796, "Stage V": 449}),
]
rows = []
for cohort, fleet, tiers in cohort_rows:
    for tier, count in tiers.items():
        rows.append({
            "cohort": cohort,
            "fleet": fleet,
            "tier": tier,
            "count": count,
            "share": round(count / fleet, 6),
            "share_pct": round((count / fleet) * 100, 2),
        })
cohort_tier_distribution = pd.DataFrame(rows)

def_rules = pd.DataFrame([
    ["Unregulated", 0, 0, 0, "No emissions controls"],
    ["Tier 1", 0, 0, 0, "Early basic regulated tier; no SCR"],
    ["Tier 2", 0, 0, 0, "No SCR"],
    ["Tier 3", 0, 0, 0, "No SCR"],
    ["Tier 4i", 1, 0, 0, "DPF transition stage; treat as non-DEF in base case"],
    ["Tier 4f", 1, 1, 1, "SCR-equipped base-case DEF-required tier"],
    ["Stage V", 1, 1, 1, "SCR-equipped base-case DEF-required tier"],
], columns=["tier", "dpf_flag", "scr_flag", "def_required_basecase", "notes"])

tier_summary.to_csv(internal / "tier_summary.csv", index=False)
cohort_tier_distribution.to_csv(internal / "cohort_tier_distribution.csv", index=False)
def_rules.to_csv(internal / "def_rules.csv", index=False)

scr = tier_summary.loc[tier_summary["tier"].isin(["Tier 4f", "Stage V"])]
derived = pd.DataFrame([{
    "active_licensed_diesel_tractors": int(tier_summary["count"].sum()),
    "total_diesel_ml": float(tier_summary["fuel_ml"].sum()),
    "def_required_tractors_basecase": int(scr["count"].sum()),
    "def_required_share_pct_basecase": round(100 * scr["count"].sum() / tier_summary["count"].sum(), 2),
    "diesel_ml_scr_basecase": float(scr["fuel_ml"].sum()),
    "def_ml_low_3pct": round(float(scr["fuel_ml"].sum()) * 0.03, 3),
    "def_ml_central_4pct": round(float(scr["fuel_ml"].sum()) * 0.04, 3),
    "def_ml_high_5pct": round(float(scr["fuel_ml"].sum()) * 0.05, 3),
}])
derived.to_csv(internal / "derived_internal_summary.csv", index=False)
print("Internal files regenerated.")

# Note: the extracted tier rows sum to 31,255 while the report text says 31,253.
