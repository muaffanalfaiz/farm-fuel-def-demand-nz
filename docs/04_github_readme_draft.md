# Farm Fuel and DEF Demand NZ

A register-informed, cohort-constrained, tier-calibrated analytical pipeline for estimating New Zealand tractor diesel demand and DEF demand.

## Current baseline
- Active licensed weighted fleet: 31,255.00
- National diesel demand: 203.800 ML
- Central DEF demand: 2.100 ML

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
