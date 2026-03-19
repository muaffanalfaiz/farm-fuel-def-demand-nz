from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def p(rel: str) -> Path:
    return ROOT / rel

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def fmt_num(x: float, decimals: int = 2) -> str:
    return f"{x:,.{decimals}f}"

def main() -> None:
    docs_dir = p("docs")
    ensure_dir(docs_dir)

    project = pd.read_csv(p("outputs/tables/project_summary.csv")).iloc[0]
    national = pd.read_csv(p("outputs/tables/national_diesel_by_tier.csv")).copy()
    scenario = pd.read_csv(p("outputs/scenarios/scenario_national_compare.csv")).copy()
    geo = pd.read_csv(p("outputs/tables/geography_qa_summary.csv")).iloc[0]
    regional = pd.read_csv(p("outputs/tables/regional_master_table.csv")).copy()

    national.columns = [c.strip().lower() for c in national.columns]
    scenario.columns = [c.strip().lower() for c in scenario.columns]
    regional.columns = [c.strip().lower() for c in regional.columns]

    if "annual_diesel_ml" not in national.columns:
        national["annual_diesel_ml"] = pd.to_numeric(national["annual_diesel_litres"], errors="coerce") / 1_000_000

    top_region = regional.sort_values("regional_diesel_ml", ascending=False).iloc[0]
    top_def_region = regional.sort_values("regional_def_central_ml", ascending=False).iloc[0]

    baseline = scenario.loc[scenario["scenario_name"] == "baseline_current_structure"].iloc[0]
    best_def = scenario.sort_values("def_central_ml", ascending=False).iloc[0]
    best_diesel = scenario.sort_values("national_diesel_ml", ascending=False).iloc[0]

    methods_text = f"""# Methods Summary

## Study objective
This project estimates New Zealand tractor diesel demand and DEF demand using a register-informed, cohort-constrained, tier-calibrated framework.

## Core logic
1. Raw NZTA diesel tractor records are used as a geographic template.
2. The active licensed tractor fleet is imposed through the internal calibrated cohort totals.
3. Cohort-tier shares are applied to produce the weighted fleet by emission tier.
4. Tier-specific litres per tractor are derived from the internal calibrated tier table.
5. National diesel demand and SCR-tier DEF demand are allocated regionally using the geographic template.

## Current calibrated baseline
- Active licensed weighted fleet: {fmt_num(project['project_active_licensed_weighted_fleet'], 2)}
- National diesel demand: {fmt_num(project['project_national_diesel_ml'], 3)} ML
- SCR-weighted tractor count: {fmt_num(project['weighted_scr_tractor_count'], 2)}
- SCR diesel demand: {fmt_num(project['scr_diesel_ml'], 3)} ML
- DEF low / central / high: {fmt_num(project['def_low_ml'], 3)} / {fmt_num(project['def_central_ml'], 3)} / {fmt_num(project['def_high_ml'], 3)} ML

## Scenario framework
The scenario engine keeps the total weighted fleet fixed and redistributes tractors across emission tiers using transparent transition rules. It is a structural scenario model, not a historical time-series forecast.
"""

    findings_text = f"""# Key Findings

## Baseline
The calibrated baseline produces:
- {fmt_num(project['project_active_licensed_weighted_fleet'], 2)} active licensed weighted tractors
- {fmt_num(project['project_national_diesel_ml'], 3)} ML national diesel demand
- {fmt_num(project['def_central_ml'], 3)} ML central DEF demand

## Tier structure
Top diesel-contributing tiers in the baseline are:
{chr(10).join([f"- {row['tier_assigned']}: {fmt_num(row['annual_diesel_ml'], 3)} ML" for _, row in national.sort_values('annual_diesel_ml', ascending=False).iterrows()])}

## Regional concentration
Top baseline diesel region:
- {top_region['region_key']}: {fmt_num(top_region['regional_diesel_ml'], 3)} ML

Top baseline DEF region:
- {top_def_region['region_key']}: {fmt_num(top_def_region['regional_def_central_ml'], 3)} ML

## Scenario interpretation
Highest DEF-demand scenario:
- {best_def['scenario_name']}
- central DEF demand: {fmt_num(best_def['def_central_ml'], 3)} ML
- increase vs baseline: {fmt_num(best_def['delta_def_central_ml_vs_baseline'], 3)} ML

Highest diesel-demand scenario:
- {best_diesel['scenario_name']}
- national diesel: {fmt_num(best_diesel['national_diesel_ml'], 3)} ML
"""

    limitations_text = f"""# Limitations

## Geographic interpretation
The regional outputs are register-based allocations derived from NZTA tractor geography. They should be interpreted as allocated demand surfaces, not direct measured operating-location fuel demand.

## Scenario interpretation
The scenario layer is structural. It redistributes the fleet across tiers while holding the total weighted fleet fixed. It is not a historical time-series forecast and does not yet include region-specific adoption behavior.

## Missing external explanatory data
The feature store scaffold is ready, but agriculture production, farm numbers, farm size, and tractor registration history files have not yet been joined.

## QA status
Current geography QA summary:
- region count: {int(geo['region_count'])}
- urban hint count: {int(geo['urban_hint_count'])}
- administrative-bias flag count: {int(geo['admin_bias_flag_count'])}
- missing region key count: {int(geo['missing_region_key_count'])}
"""

    readme_text = f"""# Farm Fuel and DEF Demand NZ

A register-informed, cohort-constrained, tier-calibrated analytical pipeline for estimating New Zealand tractor diesel demand and DEF demand.

## Current baseline
- Active licensed weighted fleet: {fmt_num(project['project_active_licensed_weighted_fleet'], 2)}
- National diesel demand: {fmt_num(project['project_national_diesel_ml'], 3)} ML
- Central DEF demand: {fmt_num(project['def_central_ml'], 3)} ML

## Main outputs
- `outputs/tables/project_summary.csv`
- `outputs/tables/regional_master_table.csv`
- `outputs/tables/regional_feature_store.csv`
- `outputs/scenarios/scenario_national_summary.csv`
- `outputs/scenarios/scenario_national_compare.csv`
- `outputs/figures/`

## Key scripts
- `scripts/05_assign_tiers.py`
- `scripts/06_estimate_diesel.py`
- `scripts/07_estimate_def.py`
- `scripts/08_build_summary.py`
- `scripts/09_validate_outputs.py`
- `scripts/10_build_regional_master_table.py`
- `scripts/11_build_feature_store.py`
- `scripts/12_geography_qa.py`
- `scripts/14_run_scenarios.py`
- `scripts/15_scenario_summary.py`
- `scripts/17_make_figures.py`

## Recommended repo narrative
This repository should be framed as a calibrated estimation and scenario-analysis project, not as a raw observational fuel-consumption dataset. The core value is the integration of register structure, cohort-tier logic, national fuel calibration, and SCR-linked DEF demand scenarios.

## Next enrichment step
Add external agriculture and registrations files into:
- `data/raw/agriculture/`
- `data/raw/nzta_registrations/`

Then rerun the feature-store and scenario-support layer.
"""

    results_snapshot_text = f"""# Results Snapshot

| Metric | Value |
|---|---:|
| Active licensed weighted fleet | {fmt_num(project['project_active_licensed_weighted_fleet'], 2)} |
| National diesel demand (ML) | {fmt_num(project['project_national_diesel_ml'], 3)} |
| Weighted SCR tractor count | {fmt_num(project['weighted_scr_tractor_count'], 2)} |
| SCR diesel demand (ML) | {fmt_num(project['scr_diesel_ml'], 3)} |
| DEF low (ML) | {fmt_num(project['def_low_ml'], 3)} |
| DEF central (ML) | {fmt_num(project['def_central_ml'], 3)} |
| DEF high (ML) | {fmt_num(project['def_high_ml'], 3)} |
| Top diesel region | {top_region['region_key']} |
| Top diesel region demand (ML) | {fmt_num(top_region['regional_diesel_ml'], 3)} |
| Top DEF region | {top_def_region['region_key']} |
| Top DEF region demand (ML) | {fmt_num(top_def_region['regional_def_central_ml'], 3)} |
"""

    (docs_dir / "01_methods_summary.md").write_text(methods_text, encoding="utf-8")
    (docs_dir / "02_key_findings.md").write_text(findings_text, encoding="utf-8")
    (docs_dir / "03_limitations.md").write_text(limitations_text, encoding="utf-8")
    (docs_dir / "04_github_readme_draft.md").write_text(readme_text, encoding="utf-8")
    (docs_dir / "05_results_snapshot.md").write_text(results_snapshot_text, encoding="utf-8")

    print("Narrative files created:")
    print("- docs/01_methods_summary.md")
    print("- docs/02_key_findings.md")
    print("- docs/03_limitations.md")
    print("- docs/04_github_readme_draft.md")
    print("- docs/05_results_snapshot.md")

if __name__ == "__main__":
    main()
