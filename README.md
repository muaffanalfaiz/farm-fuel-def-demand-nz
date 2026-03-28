# Farm Fuel & DEF Demand — New Zealand

A register-informed, cohort-constrained, tier-calibrated analytical pipeline for estimating New Zealand tractor diesel demand and Diesel Exhaust Fluid (DEF) demand, with regional allocation, structural scenario analysis, and a 2026-2030 forecast.

## Methodology

This model uses NZTA Motor Vehicle Register records as a geographic template for New Zealand's diesel tractor fleet. Rather than treating raw register counts as ground truth, the pipeline imposes independently calibrated active-licensed fleet totals by age cohort, applies cohort-to-emission-tier shares, and derives tier-specific fuel consumption from calibrated activity factors (power, hours, load factor, SFC). National diesel and DEF demand are then allocated regionally using the register's geographic distribution. Five structural scenarios explore how fleet modernisation toward SCR-equipped tiers would shift diesel and DEF demand through 2030.

## Baseline Results

| Metric | Value |
|---|---:|
| Active licensed weighted fleet | 31,255 |
| National diesel demand | 203.800 ML |
| Weighted SCR tractor count | 4,214 |
| SCR diesel demand | 52.500 ML |
| DEF demand (low / central / high) | 1.575 / 2.100 / 2.625 ML |
| Top diesel region | Auckland (16.628 ML) |

## Scenarios (2030 endpoints)

| Scenario | Diesel (ML) | Central DEF (ML) | SCR fleet |
|---|---:|---:|---:|
| Baseline (current structure) | 203.800 | 2.100 | 4,214 |
| Moderate modernisation | 217.882 | 3.037 | 5,932 |
| Accelerated modernisation | 231.290 | 3.974 | 7,649 |
| SCR push | 234.421 | 4.035 | 7,509 |
| Delayed replacement | 210.164 | 2.392 | 4,740 |

## Pipeline

Run `python run_all.py` to execute the full canonical pipeline, or run scripts individually in this order:

| # | Script | Purpose |
|---|---|---|
| 00 | `00_build_internal_files_from_report_extract.py` | Bootstrap calibrated tier/cohort/DEF tables from report extract |
| 01 | `01_download_data.py` | Download NZTA fleet ZIP and public data sources |
| 02 | `02_prepare_internal_tables.py` | Standardise internal calibration CSVs |
| 03 | `03_parse_nzta_fleet.py` | Parse NZTA fleet, filter to diesel tractors |
| 05 | `05_assign_tiers.py` | Assign emission tiers via cohort-constrained weighting |
| 06 | `06_estimate_diesel.py` | Estimate diesel demand by tier and region |
| 07 | `07_estimate_def.py` | Estimate DEF demand for SCR-equipped tiers |
| 08 | `08_build_summary.py` | Build project summary comparing outputs to calibration |
| 09 | `09_validate_outputs.py` | Run internal consistency checks |
| 10 | `10_build_regional_master_table.py` | Merge regional fleet, diesel, DEF, and tier-wide tables |
| 11 | `11_build_feature_store.py` | Build regional feature store with engineered metrics |
| 12 | `12_geography_qa.py` | Flag administrative-bias and urban-registration regions |
| 13 | `13_prepare_external_templates.py` | Create scaffolding for optional external data joins |
| 14 | `14_run_scenarios.py` | Run five tier-transition scenarios |
| 15 | `15_scenario_summary.py` | Compute scenario vs baseline deltas |
| 16 | `16_export_dashboard.py` | Export dashboard-ready CSVs |
| 17 | `17_make_figures.py` | Generate baseline and scenario charts |
| 18 | `18_write_narratives.py` | Auto-generate methods, findings, and limitations docs |
| 19 | `19_pack_release.py` | Package tables, figures, and docs into a release ZIP |
| 20 | `20_run_forecast.py` | Run 2026-2030 structural forecast by scenario |
| 21 | `21_make_forecast_figures.py` | Generate forecast trajectory charts |
| 22 | `22_write_prediction_note.py` | Auto-generate the prediction note |

## Project Structure

`
config/                  Configuration YAML (paths, DEF ratios, activity factors)
data/
  staging/               Standardised internal calibration tables
  exports/               NZTA tractor sample CSV
  reference/             TA-region lookup (placeholder)
dashboard/               Dashboard-ready CSVs for Power BI / Tableau
docs/                    Auto-generated narrative documents
outputs/
  tables/                Core analytical tables and validation checks
  scenarios/             Scenario national and regional summaries
  forecast/              2026-2030 forecast tables
  figures/               Generated PNG charts
release/                 Release manifest and packaging
scripts/                 Canonical pipeline scripts
`

## Data Sources

| Source | Type | Access |
|---|---|---|
| NZTA Motor Vehicle Register | Public | Auto-downloaded (`01_download_data.py`) |
| Internal tractor-engine-standard report | Calibration | Extracted in `00_build_internal_files_from_report_extract.py` |
| DairyNZ Statistics 2023-24 | Public | Auto-downloaded |
| Beef + Lamb NZ survey spreadsheets | Public | Manual download |
| Stats NZ / Figure.NZ agriculture tables | Public | Manual download |
| EECA off-road fuel report | Public | Manual download |

## Important Caveats

- **Regional outputs are allocated demand surfaces**, not direct measured operating-location fuel consumption. See `docs/03_limitations.md`.
- **The forecast is scenario-based structural projection**, not a historical time-series model. See `docs/06_prediction_note.md`.
- **Geography QA** flags 5 regions as possible administrative-bias locations (Auckland, Christchurch, Hamilton, Palmerston North, Invercargill).

## Requirements

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## License

This project is provided for research and portfolio purposes.
