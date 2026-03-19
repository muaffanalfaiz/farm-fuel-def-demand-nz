# Pipeline summary

## Internal sources
1. Curated unpublished report tables:
   - `tier_summary.csv`
   - `cohort_tier_distribution.csv`
   - `def_rules.csv`

## Public sources
1. NZTA fleet all-years ZIP
2. NZTA vehicle data dictionary CSV
3. NZTA tractor registrations export
4. Stats NZ / Figure.NZ agriculture region and farm tables
5. DairyNZ statistics
6. Beef + Lamb NZ survey spreadsheets
7. EECA off-road fuel report

## Analytical flow
1. Download public data
2. Standardise internal tables
3. Parse NZTA fleet
4. Filter tractors
5. Assign tiers
6. Estimate tractor-level diesel
7. Identify SCR / DEF-required tiers
8. Estimate DEF low / central / high
9. Build regional feature store
10. Fit starter model
11. Export dashboard tables
