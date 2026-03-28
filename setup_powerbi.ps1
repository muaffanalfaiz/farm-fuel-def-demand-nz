<#
.SYNOPSIS
    Set up Power BI dashboard for farm-fuel-def-demand-nz.
    Run from the repo root:
        .\setup_powerbi.ps1

.DESCRIPTION
    1. Creates powerbi/ folder structure
    2. Creates and runs Python script to export Power BI-ready flat CSVs
    3. Creates the complete Power BI build guide
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path "scripts/common.py") -or -not (Test-Path "config/paths.yaml")) {
    Write-Error "Run this script from the farm-fuel-def-demand-nz repo root."
    exit 1
}

Write-Host "`n=== STEP 1: Create folder structure ===" -ForegroundColor Cyan

New-Item -ItemType Directory -Path "powerbi/data" -Force | Out-Null
New-Item -ItemType Directory -Path "powerbi/screenshots" -Force | Out-Null
Write-Host "  Created powerbi/data/ and powerbi/screenshots/"

Write-Host "`n=== STEP 2: Create Power BI CSV export script ===" -ForegroundColor Cyan

$exportScript = @"
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
"@

Set-Content -Path "export_powerbi_csvs.py" -Value $exportScript
Write-Host "  Created export_powerbi_csvs.py"

Write-Host "`n=== STEP 3: Run the export script ===" -ForegroundColor Cyan

python export_powerbi_csvs.py

Write-Host "`n=== STEP 4: Create Power BI build guide ===" -ForegroundColor Cyan

$guide = @"
# Power BI Dashboard Build Guide — Farm Fuel & DEF Demand NZ

Complete step-by-step instructions. Follow in order.

---

## 0. Before you start

- Power BI Desktop must be installed
- You must have run ``export_powerbi_csvs.py`` first (the setup script did this)
- All data files are in ``powerbi/data/``

---

## 1. Create and save the file

1. Open **Power BI Desktop**
2. Click **Blank report**
3. **File > Save As** > navigate to your repo's ``powerbi/`` folder
4. Save as ``farm_fuel_def_demand_nz.pbix``

---

## 2. Import all data tables

For each file below, do: **Home > Get Data > Text/CSV** > navigate to ``powerbi/data/`` > select the file > click **Load** (not Transform)

Import these 7 files in order:

1. ``kpi_cards.csv``
2. ``tier_breakdown.csv``
3. ``regional_summary.csv``
4. ``scenario_summary.csv``
5. ``forecast_trajectory.csv``
6. ``forecast_tier_trajectory.csv``
7. ``forecast_regional_def_2030.csv``

After loading all 7, you should see them listed in the **Data** pane on the right side.

---

## 3. Page 1 — Fleet & Fuel Overview

### Rename the page

- Right-click the ``Page 1`` tab at the bottom
- Click **Rename**
- Type ``Fleet & Fuel Overview``
- Press Enter

### Add page title

- Click **Insert** menu at the top ribbon
- Click **Text box**
- Type: ``NZ Tractor Fleet: Diesel & DEF Demand``
- Select the text, set font size to **20**, click **Bold**
- Drag the text box to the **top-left** of the canvas

### Add KPI cards (6 cards)

You will create 6 cards. For each one:

**Card 1 — Active Licensed Fleet:**

1. Click a **blank area** of the canvas
2. In the **Visualizations** pane (right side), click the **Card** icon (rectangle with a number, first row, 4th from left)
3. A blank card appears on the canvas
4. In the **Data** pane (far right), expand ``kpi_cards``
5. Drag ``value`` into the **Fields** well (where it says "Add data fields here")
6. The card shows a sum of all values — you need to filter it to one row
7. In the **Filters** pane (middle-right panel), look under **Filters on this visual**
8. Drag ``metric`` from ``kpi_cards`` into the filter area
9. Set filter type to **Basic filtering**
10. Tick **only** ``Active Licensed Fleet``
11. The card now shows ``31255``
12. Click the card. In **Format visual** (paint roller icon) > **Callout value** > change **Display units** to ``None``
13. Click **Category label** > toggle **On** (this shows "Active Licensed Fleet" under the number)
14. Resize the card to roughly 1/6th of the canvas width
15. Place it at the top-left under the title

**Card 2 — National Diesel Demand:**

1. Click blank canvas area
2. Click **Card** icon in Visualizations
3. Drag ``value`` from ``kpi_cards`` to **Fields**
4. In **Filters on this visual**, drag ``metric``, tick only ``National Diesel Demand``
5. Card shows ``203.8``
6. Format: Display units ``None``, Category label **On**
7. Place next to Card 1

**Card 3 — Central DEF Demand:**

1. Same process: Card > ``value`` > filter to ``Central DEF Demand``
2. Shows ``2.1``
3. Place next to Card 2

**Card 4 — SCR Tractor Count:**

1. Same process: filter to ``SCR Tractor Count``
2. Shows ``4214``
3. Place next to Card 3

**Card 5 — Regions Modelled:**

1. Same process: filter to ``Regions Modelled``
2. Shows ``67``
3. Place next to Card 4

**Card 6 — Validation Checks Passed:**

1. Same process: filter to ``Validation Checks Passed``
2. Shows ``7``
3. Place next to Card 5

Arrange all 6 cards in a row below the title.

### Add diesel-by-tier bar chart

1. Click blank canvas area
2. In **Visualizations**, click **Clustered bar chart** (horizontal bars icon, first row)
3. In **Data** pane, expand ``tier_breakdown``
4. Drag ``tier`` to **Y-axis**
5. Drag ``diesel_ml`` to **X-axis**
6. Click the chart. Click the three dots ``...`` at the top-right of the chart
7. Click **Sort axis** > **diesel_ml** > then click ``...`` again > **Sort descending**
8. Click **Format visual** (paint roller) > **Title** > change text to ``Diesel Demand by Emission Tier (ML)``
9. Resize to fill the **left half** of the canvas below the KPI cards

### Add fleet-by-tier bar chart

1. Click blank canvas area
2. Click **Clustered bar chart**
3. Drag ``tier`` from ``tier_breakdown`` to **Y-axis**
4. Drag ``fleet_count`` to **X-axis**
5. Sort by fleet_count descending (three dots > Sort axis > fleet_count > Sort descending)
6. Title: ``Active Licensed Fleet by Emission Tier``
7. Resize to fill the **right half** of the canvas below the KPI cards

### Add tier slicer (optional)

1. Click blank area > click **Slicer** icon (funnel shape, second row in Visualizations)
2. Drag ``scr_flag`` from ``tier_breakdown`` to **Field**
3. This lets users filter to SCR-only or non-SCR tiers
4. Place at the bottom-right

---

## 4. Page 2 — Regional Analysis

### Create the page

- Click the **+** icon at the bottom to create a new page
- Right-click the new tab > **Rename** > type ``Regional Analysis``

### Add page title

- Insert > Text box > type ``Regional Diesel & DEF Demand``
- Font size 16, bold, place at top

### Top 15 regions by diesel (horizontal bar chart)

1. Click blank area > click **Clustered bar chart**
2. Expand ``regional_summary`` in Data pane
3. Drag ``region_key`` to **Y-axis**
4. Drag ``regional_diesel_ml`` to **X-axis**
5. In **Filters** pane > **Filters on this visual** > drag ``rank`` > set filter to ``is less than or equal to`` ``15``
6. Sort by regional_diesel_ml descending
7. Title: ``Top 15 Regions by Diesel Demand (ML)``
8. Resize to fill left half of canvas

### Top 15 regions by DEF (horizontal bar chart)

1. Click blank area > click **Clustered bar chart**
2. Drag ``region_key`` from ``regional_summary`` to **Y-axis**
3. Drag ``regional_def_central_ml`` to **X-axis**
4. Filter: ``rank`` is less than or equal to 15
5. Sort by regional_def_central_ml descending
6. Title: ``Top 15 Regions by Central DEF Demand (ML)``
7. Resize to fill right half of canvas

### Add admin-bias flag indicator

1. Click blank area > click **Table** visual (grid icon in Visualizations)
2. Drag ``region_key``, ``regional_diesel_ml``, ``regional_def_central_ml``, ``admin_bias_flag`` from ``regional_summary``
3. In **Filters on this visual** > drag ``admin_bias_flag`` > tick only ``1``
4. Title: ``Administrative-Bias Flagged Regions``
5. Place at the bottom of the canvas

---

## 5. Page 3 — Scenario Comparison

### Create the page

- Click **+** > Rename > ``Scenario Comparison``

### Add page title

- Insert > Text box > ``Scenario Analysis: Fleet Modernisation Pathways``
- Font 16, bold, top of canvas

### Diesel by scenario (bar chart)

1. Click blank area > **Clustered bar chart**
2. Expand ``scenario_summary`` in Data pane
3. Drag ``scenario_label`` to **Y-axis**
4. Drag ``national_diesel_ml`` to **X-axis**
5. Sort by national_diesel_ml descending
6. Title: ``National Diesel Demand by Scenario (ML)``
7. Resize to fill left half of canvas, top section

### DEF by scenario (bar chart)

1. Click blank area > **Clustered bar chart**
2. Drag ``scenario_label`` from ``scenario_summary`` to **Y-axis**
3. Drag ``def_central_ml`` to **X-axis**
4. Sort by def_central_ml descending
5. Title: ``Central DEF Demand by Scenario (ML)``
6. Resize to fill right half of canvas, top section

### SCR share comparison (bar chart)

1. Click blank area > **Clustered bar chart**
2. Drag ``scenario_label`` to **Y-axis**
3. Drag ``scr_share_pct`` to **X-axis**
4. Sort by scr_share_pct descending
5. Title: ``SCR Fleet Share by Scenario (%)``
6. Resize to fill left half, bottom section

### Scenario details table

1. Click blank area > click **Table** visual
2. Drag these fields from ``scenario_summary``:
   - ``scenario_label``
   - ``national_diesel_ml``
   - ``def_central_ml``
   - ``national_scr_tractor_count``
   - ``scr_share_pct``
3. Title: ``Scenario Endpoint Summary``
4. Place at the bottom-right

---

## 6. Page 4 — Forecast 2026-2030

### Create the page

- Click **+** > Rename > ``Forecast 2026-2030``

### Add page title

- Insert > Text box > ``Structural Forecast: 2026-2030``
- Font 16, bold, top of canvas

### Diesel trajectory line chart

1. Click blank area > click **Line chart** (first row, 2nd icon in Visualizations)
2. Expand ``forecast_trajectory`` in Data pane
3. Drag ``year`` to **X-axis**
4. Drag ``national_diesel_ml`` to **Y-axis**
5. Drag ``scenario_label`` to **Legend**
6. Click **Format visual** > **X-axis** > set **Type** to ``Categorical`` (so it shows 2026, 2027... not a continuous range)
7. Title: ``National Diesel Demand Trajectory (ML)``
8. Resize to fill left half, top section

### DEF trajectory line chart

1. Click blank area > click **Line chart**
2. Drag ``year`` from ``forecast_trajectory`` to **X-axis**
3. Drag ``def_central_ml`` to **Y-axis**
4. Drag ``scenario_label`` to **Legend**
5. X-axis type: ``Categorical``
6. Title: ``Central DEF Demand Trajectory (ML)``
7. Resize to fill right half, top section

### SCR tractor count trajectory

1. Click blank area > click **Line chart**
2. Drag ``year`` from ``forecast_trajectory`` to **X-axis**
3. Drag ``national_scr_tractor_count`` to **Y-axis**
4. Drag ``scenario_label`` to **Legend**
5. X-axis type: ``Categorical``
6. Title: ``Weighted SCR Tractor Count Trajectory``
7. Resize to fill left half, bottom section

### 2030 endpoint comparison table

1. Click blank area > click **Table** visual
2. From ``forecast_trajectory``:
   - Drag ``scenario_label``
   - Drag ``national_diesel_ml``
   - Drag ``def_central_ml``
   - Drag ``national_scr_tractor_count``
3. In **Filters on this visual** > drag ``year`` > set to ``is`` ``2030``
4. Title: ``2030 Forecast Endpoints``
5. Place at the bottom-right

---

## 7. Final steps

### Save

Press **Ctrl+S** to save the ``.pbix`` file.

### Take screenshots

For each page:
1. Click the page tab
2. Press **Windows + Shift + S** to open snipping tool
3. Select the full canvas area
4. Save each screenshot as:
   - ``powerbi/screenshots/01_fleet_fuel_overview.png``
   - ``powerbi/screenshots/02_regional_analysis.png``
   - ``powerbi/screenshots/03_scenario_comparison.png``
   - ``powerbi/screenshots/04_forecast_2026_2030.png``

### Push to GitHub

```
git add -A
git commit -m "Add Power BI dashboard with 4 pages and screenshots"
git push
```

---

## Data table reference

| File | Rows | Used on page | Purpose |
|---|---|---|---|
| ``kpi_cards.csv`` | 8 | Page 1 | KPI card values |
| ``tier_breakdown.csv`` | 7 | Page 1 | Tier-level fleet and diesel |
| ``regional_summary.csv`` | 67 | Page 2 | Regional diesel, DEF, QA flags |
| ``scenario_summary.csv`` | 5 | Page 3 | Scenario endpoints and deltas |
| ``forecast_trajectory.csv`` | 25 | Page 4 | 5 scenarios x 5 years national |
| ``forecast_tier_trajectory.csv`` | 175 | (optional) | 5 scenarios x 5 years x 7 tiers |
| ``forecast_regional_def_2030.csv`` | varies | (optional) | Top 15 regional DEF by scenario in 2030 |
"@

Set-Content -Path "powerbi/POWERBI_BUILD_GUIDE.md" -Value $guide
Write-Host "  Created powerbi/POWERBI_BUILD_GUIDE.md"

Write-Host "`n=== STEP 5: Stage changes ===" -ForegroundColor Cyan

git add -A
Write-Host "  All changes staged."

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  DONE." -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "  Power BI data files are in: powerbi/data/" -ForegroundColor Green
Write-Host "  Build guide is at: powerbi/POWERBI_BUILD_GUIDE.md" -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "  Next steps:" -ForegroundColor Green
Write-Host "    1. Open Power BI Desktop" -ForegroundColor Green
Write-Host "    2. Follow powerbi/POWERBI_BUILD_GUIDE.md" -ForegroundColor Green
Write-Host "    3. After building, take screenshots" -ForegroundColor Green
Write-Host "    4. Commit and push:" -ForegroundColor Green
Write-Host '       git commit -m "Add Power BI dashboard setup"' -ForegroundColor Green
Write-Host "       git push" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
