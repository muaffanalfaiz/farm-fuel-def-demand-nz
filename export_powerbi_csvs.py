"""
Power BI Dashboard CSV Export
Exports flat tables from existing outputs into powerbi/data/
Run from repo root: python export_powerbi_csvs.py
"""
from __future__ import annotations
import pandas as pd
import os

OUTPUTS = "outputs"
DASHBOARD = "dashboard"
PBI = "powerbi/data"
os.makedirs(PBI, exist_ok=True)

# ── Load source files ──────────────────────────────────────────────────────
print("Loading source files...")
project      = pd.read_csv(f"{DASHBOARD}/project_summary.csv")
tiers_diesel = pd.read_csv(f"{OUTPUTS}/tables/national_diesel_by_tier.csv")
tier_counts  = pd.read_csv(f"{OUTPUTS}/tables/tier_counts_assigned_weighted.csv")
regional     = pd.read_csv(f"{DASHBOARD}/regional_master_table.csv")
qa_summary   = pd.read_csv(f"{DASHBOARD}/geography_qa_summary.csv")
qa_flags     = pd.read_csv(f"{DASHBOARD}/geography_qa_flags.csv")
scen_nat     = pd.read_csv(f"{DASHBOARD}/scenario_national_summary.csv")
scen_compare = pd.read_csv(f"{DASHBOARD}/scenario_national_compare.csv")
forecast_nat = pd.read_csv(f"{DASHBOARD}/forecast_national_annual.csv")
forecast_tier= pd.read_csv(f"{DASHBOARD}/forecast_national_by_tier_annual.csv")
forecast_reg = pd.read_csv(f"{DASHBOARD}/forecast_top15_regional_def_2030.csv")
validation   = pd.read_csv(f"{DASHBOARD}/validation_checks.csv")

# Normalise columns
for df in [project, tiers_diesel, tier_counts, regional, qa_summary, qa_flags,
           scen_nat, scen_compare, forecast_nat, forecast_tier, forecast_reg, validation]:
    df.columns = [c.strip().lower() for c in df.columns]

# ── Table 1: kpi_cards.csv ─────────────────────────────────────────────────
p = project.iloc[0]
qa = qa_summary.iloc[0]
kpi = pd.DataFrame([
    {"metric": "Active Licensed Fleet",    "value": round(p["project_active_licensed_weighted_fleet"]),    "unit": "tractors"},
    {"metric": "National Diesel Demand",   "value": round(p["project_national_diesel_ml"], 1),            "unit": "ML"},
    {"metric": "Central DEF Demand",       "value": round(p["def_central_ml"], 3),                        "unit": "ML"},
    {"metric": "SCR Tractor Count",        "value": round(p["weighted_scr_tractor_count"]),               "unit": "tractors"},
    {"metric": "SCR Diesel Demand",        "value": round(p["scr_diesel_ml"], 1),                         "unit": "ML"},
    {"metric": "Regions Modelled",         "value": int(qa["region_count"]),                               "unit": "regions"},
    {"metric": "Admin-Bias Flags",         "value": int(qa["admin_bias_flag_count"]),                      "unit": "regions"},
    {"metric": "Validation Checks Passed", "value": int(validation["pass"].sum()),                         "unit": f"of {len(validation)}"},
])
kpi.to_csv(f"{PBI}/kpi_cards.csv", index=False)
print(f"  kpi_cards.csv -> {len(kpi)} rows")

# ── Table 2: tier_breakdown.csv ────────────────────────────────────────────
if "annual_diesel_litres" in tiers_diesel.columns:
    tiers_diesel["diesel_ml"] = tiers_diesel["annual_diesel_litres"] / 1_000_000
elif "annual_diesel_ml" in tiers_diesel.columns:
    tiers_diesel["diesel_ml"] = tiers_diesel["annual_diesel_ml"]

tier_order = ["Unregulated", "Tier 1", "Tier 2", "Tier 3", "Tier 4i", "Tier 4f", "Stage V"]
tb = tiers_diesel[["tier_assigned", "weighted_tractor_count", "diesel_ml"]].copy()
tb = tb.rename(columns={"tier_assigned": "tier", "weighted_tractor_count": "fleet_count"})
tb["fleet_count"] = tb["fleet_count"].round(0).astype(int)
tb["diesel_ml"] = tb["diesel_ml"].round(3)
total_diesel = tb["diesel_ml"].sum()
tb["diesel_share_pct"] = (tb["diesel_ml"] / total_diesel * 100).round(1)
total_fleet = tb["fleet_count"].sum()
tb["fleet_share_pct"] = (tb["fleet_count"] / total_fleet * 100).round(1)

scr_tiers = {"Tier 4f", "Stage V"}
tb["scr_flag"] = tb["tier"].isin(scr_tiers).astype(int)
tb["def_flag"] = tb["tier"].isin(scr_tiers).astype(int)
tb["tier_order"] = tb["tier"].map({t: i for i, t in enumerate(tier_order)})
tb = tb.sort_values("tier_order").drop(columns=["tier_order"])
tb.to_csv(f"{PBI}/tier_breakdown.csv", index=False)
print(f"  tier_breakdown.csv -> {len(tb)} rows")

# ── Table 3: regional_summary.csv ──────────────────────────────────────────
keep_cols = [
    "region_key",
    "regional_active_licensed_count",
    "regional_diesel_ml",
    "regional_scr_diesel_ml",
    "regional_def_central_ml",
    "share_of_national_fleet",
    "share_of_national_diesel",
    "share_of_national_def_central",
]
rc = regional[[c for c in keep_cols if c in regional.columns]].copy()
rc = rc.sort_values("regional_diesel_ml", ascending=False).reset_index(drop=True)
rc["rank"] = range(1, len(rc) + 1)

# Round for readability
for c in ["regional_diesel_ml", "regional_scr_diesel_ml", "regional_def_central_ml"]:
    if c in rc.columns:
        rc[c] = rc[c].round(3)
for c in ["share_of_national_fleet", "share_of_national_diesel", "share_of_national_def_central"]:
    if c in rc.columns:
        rc[c] = (rc[c] * 100).round(2)
if "regional_active_licensed_count" in rc.columns:
    rc["regional_active_licensed_count"] = rc["regional_active_licensed_count"].round(0).astype(int)

# Add QA flags
if "region_key" in qa_flags.columns:
    flagged = set(qa_flags["region_key"].unique())
    rc["admin_bias_flag"] = rc["region_key"].isin(flagged).astype(int)
else:
    rc["admin_bias_flag"] = 0

rc.to_csv(f"{PBI}/regional_summary.csv", index=False)
print(f"  regional_summary.csv -> {len(rc)} rows")

# ── Table 4: scenario_summary.csv ─────────────────────────────────────────
sc = scen_compare.copy()
# Clean scenario names for display
name_map = {
    "baseline_current_structure": "Baseline",
    "moderate_modernization": "Moderate Modernisation",
    "accelerated_modernization": "Accelerated Modernisation",
    "scr_push": "SCR Push",
    "delayed_replacement": "Delayed Replacement",
}
sc["scenario_label"] = sc["scenario_name"].map(name_map).fillna(sc["scenario_name"])

keep = ["scenario_name", "scenario_label",
        "national_diesel_ml", "def_central_ml",
        "national_scr_tractor_count", "scr_share_pct", "modern_tiers_share_pct"]
delta_cols = [c for c in sc.columns if c.startswith("delta_") or c.startswith("pct_delta_")]
keep = keep + delta_cols
sc = sc[[c for c in keep if c in sc.columns]].copy()

for c in ["national_diesel_ml", "def_central_ml"]:
    if c in sc.columns:
        sc[c] = sc[c].round(3)
for c in ["national_scr_tractor_count"]:
    if c in sc.columns:
        sc[c] = sc[c].round(0).astype(int)
for c in ["scr_share_pct", "modern_tiers_share_pct"]:
    if c in sc.columns:
        sc[c] = sc[c].round(1)

sc.to_csv(f"{PBI}/scenario_summary.csv", index=False)
print(f"  scenario_summary.csv -> {len(sc)} rows")

# ── Table 5: forecast_trajectory.csv ───────────────────────────────────────
ft = forecast_nat.copy()
ft["scenario_label"] = ft["scenario_name"].map(name_map).fillna(ft["scenario_name"])
for c in ["national_diesel_ml", "def_central_ml", "def_low_ml", "def_high_ml"]:
    if c in ft.columns:
        ft[c] = ft[c].round(3)
for c in ["national_scr_tractor_count", "national_weighted_fleet"]:
    if c in ft.columns:
        ft[c] = ft[c].round(0).astype(int)
ft.to_csv(f"{PBI}/forecast_trajectory.csv", index=False)
print(f"  forecast_trajectory.csv -> {len(ft)} rows")

# ── Table 6: forecast_tier_trajectory.csv ──────────────────────────────────
ftt = forecast_tier.copy()
ftt["scenario_label"] = ftt["scenario_name"].map(name_map).fillna(ftt["scenario_name"])
ftt["weighted_tractor_count"] = ftt["weighted_tractor_count"].round(0).astype(int)
ftt["annual_diesel_ml"] = ftt["annual_diesel_ml"].round(3)
ftt.to_csv(f"{PBI}/forecast_tier_trajectory.csv", index=False)
print(f"  forecast_tier_trajectory.csv -> {len(ftt)} rows")

# ── Table 7: forecast_regional_def_2030.csv ────────────────────────────────
fr = forecast_reg.copy()
fr["scenario_label"] = fr["scenario_name"].map(name_map).fillna(fr["scenario_name"])
for c in ["regional_diesel_ml", "regional_scr_diesel_ml", "regional_def_central_ml", "def_low_ml", "def_high_ml"]:
    if c in fr.columns:
        fr[c] = fr[c].round(3)
fr.to_csv(f"{PBI}/forecast_regional_def_2030.csv", index=False)
print(f"  forecast_regional_def_2030.csv -> {len(fr)} rows")

print(f"\nAll done. Files saved to: {PBI}/")
print("Next: open Power BI Desktop and follow powerbi/POWERBI_BUILD_GUIDE.md")
