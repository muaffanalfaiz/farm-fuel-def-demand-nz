# Methods Summary

## Study objective
This project estimates New Zealand tractor diesel demand and DEF demand using a register-informed, cohort-constrained, tier-calibrated framework.

## Core logic
1. Raw NZTA diesel tractor records are used as a geographic template.
2. The active licensed tractor fleet is imposed through the internal calibrated cohort totals.
3. Cohort-tier shares are applied to produce the weighted fleet by emission tier.
4. Tier-specific litres per tractor are derived from the internal calibrated tier table.
5. National diesel demand and SCR-tier DEF demand are allocated regionally using the geographic template.

## Current calibrated baseline
- Active licensed weighted fleet: 31,255.00
- National diesel demand: 203.800 ML
- SCR-weighted tractor count: 4,214.00
- SCR diesel demand: 52.500 ML
- DEF low / central / high: 1.575 / 2.100 / 2.625 ML

## Scenario framework
The scenario engine keeps the total weighted fleet fixed and redistributes tractors across emission tiers using transparent transition rules. It is a structural scenario model, not a historical time-series forecast.
