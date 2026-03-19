# Farm Fuel & DEF Demand NZ

Starter repo for an end-to-end pipeline to estimate, model, and forecast diesel and DEF demand for New Zealand's tractor fleet.

## Run order
1. `python scripts/01_download_data.py`
2. Add your internal curated tables from the unpublished tractor-engine-standard report into `data/raw/internal/`
3. `python scripts/02_prepare_internal_tables.py`
4. `python scripts/03_parse_nzta_fleet.py`
5. `python scripts/04_build_reference_tables.py`
6. `python scripts/05_assign_tiers.py`
7. `python scripts/06_estimate_diesel.py`
8. `python scripts/07_estimate_def.py`
9. `python scripts/08_build_feature_store.py`
10. `python scripts/09_forecast.py`
11. `python scripts/10_export_dashboard.py`

## Notes
- This starter intentionally keeps the unpublished report out of any public citation workflow.
- Public data sources should be downloaded from the official source pages or direct file URLs configured in `config/paths.yaml`.
- The pipeline expects Python 3.11+.
