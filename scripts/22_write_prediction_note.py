from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def p(rel: str) -> Path:
    return ROOT / rel

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def fmt(x: float, d: int = 3) -> str:
    return f"{x:,.{d}f}"

def main() -> None:
    docs_dir = p("docs")
    ensure_dir(docs_dir)

    forecast = pd.read_csv(p("outputs/forecast/forecast_national_annual.csv")).copy()
    forecast.columns = [c.strip().lower() for c in forecast.columns]

    end_year = int(forecast["year"].max())
    end_df = forecast.loc[forecast["year"] == end_year].copy()

    baseline = end_df.loc[end_df["scenario_name"] == "baseline_current_structure"].iloc[0]
    best_def = end_df.sort_values("def_central_ml", ascending=False).iloc[0]
    best_scr = end_df.sort_values("national_scr_tractor_count", ascending=False).iloc[0]
    lowest = end_df.sort_values("def_central_ml", ascending=True).iloc[0]

    text = f"""# Prediction Note

## What this forecast is
This is a structural year-by-year forecast from {int(forecast['year'].min())} to {end_year}. It interpolates from the calibrated baseline fleet structure toward each scenario end-state while preserving the total weighted fleet.

## What this forecast is not
This is not a historical time-series forecasting model trained on observed annual diesel demand. It is a scenario-based projection using the calibrated tier structure and tier-specific fuel intensity assumptions.

## {end_year} forecast endpoints
Baseline continuation:
- National diesel: {fmt(baseline['national_diesel_ml'])} ML
- Central DEF: {fmt(baseline['def_central_ml'])} ML
- Weighted SCR tractor count: {fmt(baseline['national_scr_tractor_count'], 2)}

Highest DEF-demand scenario:
- Scenario: {best_def['scenario_name']}
- National diesel: {fmt(best_def['national_diesel_ml'])} ML
- Central DEF: {fmt(best_def['def_central_ml'])} ML
- Weighted SCR tractor count: {fmt(best_def['national_scr_tractor_count'], 2)}

Highest SCR-fleet scenario:
- Scenario: {best_scr['scenario_name']}
- Weighted SCR tractor count: {fmt(best_scr['national_scr_tractor_count'], 2)}
- Central DEF: {fmt(best_scr['def_central_ml'])} ML

Lowest DEF-demand scenario:
- Scenario: {lowest['scenario_name']}
- Central DEF: {fmt(lowest['def_central_ml'])} ML

## Interpretation
Under the current calibrated assumptions, stronger modernization and SCR adoption increase projected DEF demand substantially. This is because the scenario engine shifts a larger share of the active fleet into Tier 4f and Stage V, which are treated as SCR-linked DEF-demand tiers in the project framework.
"""
    (docs_dir / "06_prediction_note.md").write_text(text, encoding="utf-8")

    print("Prediction note refreshed:")
    print("- docs/06_prediction_note.md")

if __name__ == "__main__":
    main()
