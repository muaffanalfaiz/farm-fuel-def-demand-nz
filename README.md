# Register-Informed Tractor Diesel & DEF Demand Model

### New Zealand National Fleet

> **If New Zealand's tractor fleet modernises toward cleaner emission tiers, how much Diesel Exhaust Fluid will the agricultural sector need — and where?**
> This project builds a calibrated answer using NZTA fleet data, emission tier engineering, and structural scenario analysis.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-green?style=flat-square)](https://pandas.pydata.org)
[![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-yellow?style=flat-square)](powerbi/)
[![Manuscript](https://img.shields.io/badge/Manuscript-In%20Preparation-lightgrey?style=flat-square)](docs/)

---

## The problem

New Zealand has no published dataset that directly measures how much diesel its ~31,000 active tractor fleet consumes, let alone how much DEF (AdBlue) is needed as newer SCR-equipped engines replace older tiers. Fleet modernisation is happening, but the demand implications for fuel distributors, farm supply chains, and emissions policy are unquantified at the regional level.

**This project asks:** can we estimate current diesel and DEF demand from the fleet register structure, and project how that demand shifts under different modernisation scenarios through 2030?

---

## What I built

A register-informed, cohort-constrained, tier-calibrated estimation pipeline that works in three layers:

| Layer | What it does | Data source |
|---|---|---|
| Geographic template | Uses raw NZTA diesel tractor registrations as a spatial scaffolding across 67 regions | NZTA Motor Vehicle Register |
| Calibration constraint | Imposes independently calibrated active-licensed fleet totals by age cohort and emission tier | Internal tractor-engine-standard report |
| Fuel & DEF estimation | Derives tier-specific fuel intensity from power, hours, load factor, and SFC; applies DEF ratios to SCR tiers | Calibrated activity factors |

This design avoids naïvely counting raw register rows as active tractors. Instead, the register provides geographic shares while calibrated totals control the national fleet and fuel numbers — a stronger research approach than direct register counting.

---

## Key findings

### Calibrated baseline (current fleet structure)

| Metric | Value |
|---|---|
| Active licensed weighted fleet | **31,255** tractors |
| National diesel demand | **203.8 ML** |
| SCR-equipped tractor count (Tier 4f + Stage V) | **4,214** (13.5% of fleet) |
| Central DEF demand | **2.100 ML** |
| DEF demand range (low / high) | 1.575 – 2.625 ML |
| Top diesel region | Auckland (16.6 ML) |
| Regions modelled | 67 |
| Internal validation checks passed | 7 of 7 |

### Tier structure — where the diesel goes

| Tier | Fleet | Diesel (ML) | Share of national diesel |
|---|---:|---:|---:|
| Tier 3 | 13,314 | 96.5 | 47.4% |
| Tier 4f | 3,498 | 38.4 | 18.8% |
| Tier 4i | 5,259 | 26.2 | 12.9% |
| Tier 2 | 5,329 | 16.8 | 8.2% |
| Stage V | 716 | 14.1 | 6.9% |
| Unregulated | 2,175 | 8.5 | 4.2% |
| Tier 1 | 964 | 3.3 | 1.6% |

Tier 3 alone accounts for nearly half of all tractor diesel demand despite being 43% of the fleet — a consequence of higher activity hours on mid-tier commercial tractors.

### Scenario analysis — what happens as the fleet modernises?

Five structural scenarios redistribute the fleet across emission tiers while holding total fleet size fixed:

| Scenario | Diesel (ML) | Central DEF (ML) | SCR fleet share |
|---|---:|---:|---:|
| Baseline (current structure) | 203.8 | 2.100 | 13.5% |
| Moderate modernisation | 217.9 | 3.037 | 19.0% |
| Accelerated modernisation | 231.3 | 3.974 | 24.5% |
| **SCR push** | **234.4** | **4.035** | **24.0%** |
| Delayed replacement | 210.2 | 2.392 | 15.2% |

Under an SCR push scenario, DEF demand nearly doubles from 2.1 to 4.0 ML — a 92% increase driven entirely by fleet composition shifts, not fleet growth.

### 2026–2030 structural forecast

The forecast linearly interpolates from baseline to each scenario endpoint, preserving total weighted fleet:

| Scenario (2030) | Diesel (ML) | Central DEF (ML) | SCR tractors |
|---|---:|---:|---:|
| Baseline (flat) | 203.8 | 2.100 | 4,214 |
| Moderate modernisation | 217.9 | 3.037 | 5,932 |
| Accelerated modernisation | 231.3 | 3.974 | 7,649 |
| SCR push | 234.4 | 4.035 | 7,509 |
| Delayed replacement | 210.2 | 2.392 | 4,740 |

This is a scenario-based structural projection, not a time-series forecast trained on historical fuel purchases. See `docs/06_prediction_note.md` for full methodology.

### Geography QA

The pipeline flags 5 regions as potential administrative-bias locations where tractor registrations concentrate at dealerships rather than on farms: Auckland, Christchurch City, Hamilton City, Palmerston North City, and Invercargill City. Regional outputs should be interpreted as allocated demand surfaces, not direct operating-location fuel consumption.

---

## Repository structure

```
farm-fuel-def-demand-nz/
│
├── README.md
├── CITATION.cff
├── run_all.py                         # Canonical pipeline orchestrator
│
├── config/
│   ├── paths.yaml                     # Data source URLs and file paths
│   ├── def_assumptions.yaml           # DEF ratio assumptions (3%/4%/5%)
│   └── activity_factors.yaml          # Tier-specific power, hours, load, SFC
│
├── data/
│   ├── staging/                       # Standardised internal calibration tables
│   ├── exports/                       # NZTA tractor sample CSV
│   └── reference/                     # TA-region lookup
│
├── scripts/
│   ├── 00–03                          # Data acquisition and parsing
│   ├── 05–07                          # Tier assignment, diesel, DEF estimation
│   ├── 08–12                          # Summary, validation, regional master, QA
│   ├── 13–15                          # External templates, scenarios, comparison
│   ├── 16–19                          # Dashboard export, figures, narratives, release
│   └── 20–22                          # Forecast, forecast figures, prediction note
│
├── outputs/
│   ├── tables/                        # Core analytical tables and validation checks
│   ├── scenarios/                     # 5 scenario national/regional summaries
│   ├── forecast/                      # 2026–2030 forecast tables
│   └── figures/                       # Generated PNG charts
│
├── dashboard/                         # Dashboard-ready CSVs for Power BI
├── powerbi/                           # Power BI .pbix file and screenshots
├── docs/                              # Auto-generated methods, findings, limitations
└── release/                           # Release manifest and packaging
```

---

## How to reproduce

```bash
# 1. Clone the repo
git clone https://github.com/muaffanalfaiz/farm-fuel-def-demand-nz.git
cd farm-fuel-def-demand-nz

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the full pipeline
python run_all.py

# Or resume from a specific step
python run_all.py --from 14
```

The pipeline expects Python 3.11+. The NZTA fleet file is auto-downloaded. Some supplementary sources (Stats NZ, DairyNZ, Beef+Lamb, EECA) require manual download — see `config/paths.yaml`.

---

## Dashboard

A 4-page Power BI dashboard provides interactive exploration:

- **Fleet & Fuel Overview** — 6 KPI cards, diesel and fleet by emission tier
- **Regional Analysis** — top regions by diesel and DEF demand, admin-bias flags
- **Scenario Comparison** — diesel, DEF, and SCR share across 5 modernisation pathways
- **Forecast 2026–2030** — trajectory line charts for diesel, DEF, and SCR fleet

*Dashboard `.pbix` file and screenshots in `powerbi/`.*

---

## Data sources

| Source | Coverage | Access |
|---|---|---|
| [NZTA Motor Vehicle Register](https://opendata-nzta.opendata.arcgis.com/) | All registered vehicles, NZ | Public (auto-downloaded) |
| Internal tractor-engine-standard report | Calibrated tier/cohort/fuel totals | Extracted in `scripts/00_build_internal_files_from_report_extract.py` |
| [DairyNZ Statistics 2023-24](https://www.dairynz.co.nz/) | Dairy farm structure | Public PDF (auto-downloaded) |
| [Beef + Lamb NZ](https://beeflambnz.com/) | Sheep/beef farm economics | Public spreadsheets (manual) |
| [Stats NZ / Figure.NZ](https://figure.nz/) | Agricultural production by region | Public (manual) |
| [EECA](https://www.eeca.govt.nz/) | Off-road liquid fuel report | Public (manual) |

---

## Limitations

- **Regional outputs are allocated demand surfaces**, not direct on-farm fuel measurements. See `docs/03_limitations.md`.
- **The forecast is scenario-based structural projection**, not a time-series model. It assumes fixed fleet size and uses linear interpolation between baseline and scenario endpoints.
- **DEF ratios (3%/4%/5% of SCR diesel)** are assumption-driven, not learned from observed DEF purchases. Real-world variation may be wider.
- **Activity hours increase monotonically with tier** (40 hrs/yr for Unregulated to 829 hrs/yr for Stage V), reflecting the assumption that newer tractors go to larger, more intensive operations. This is the single most influential assumption in the model.
- **5 regions flagged for administrative bias** — registration geography may not reflect operating geography.

---

## Publication status

Manuscript in preparation.
Developed in collaboration with Dr Majeed Safa, Lincoln University, New Zealand.

---

## About

Built by **Muaffan Alfaiz Wisaksono**
MSc Precision Agriculture (with High Distinction), Lincoln University, New Zealand
LPDP Scholar | GIS Analyst | Precision Agriculture Researcher
8× Scopus-indexed publications

[LinkedIn](https://linkedin.com/in/muaffanalfaiz) · [GitHub](https://github.com/muaffanalfaiz)

---

*This project is part of a portfolio demonstrating applied geospatial data science for agricultural resource estimation, scenario modelling, and decision-support systems.*
