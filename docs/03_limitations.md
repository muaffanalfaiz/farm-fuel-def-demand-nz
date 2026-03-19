# Limitations

## Geographic interpretation
The regional outputs are register-based allocations derived from NZTA tractor geography. They should be interpreted as allocated demand surfaces, not direct measured operating-location fuel demand.

## Scenario interpretation
The scenario layer is structural. It redistributes the fleet across tiers while holding the total weighted fleet fixed. It is not a historical time-series forecast and does not yet include region-specific adoption behavior.

## Missing external explanatory data
The feature store scaffold is ready, but agriculture production, farm numbers, farm size, and tractor registration history files have not yet been joined.

## QA status
Current geography QA summary:
- region count: 67
- urban hint count: 14
- administrative-bias flag count: 5
- missing region key count: 1
