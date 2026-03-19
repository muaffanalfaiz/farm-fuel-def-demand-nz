from __future__ import annotations
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

def p(rel: str) -> Path:
    return ROOT / rel

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def save_line(df, x_col, y_col, series_col, title, ylabel, outpath):
    plt.figure(figsize=(10, 6))
    for name, grp in df.groupby(series_col):
        grp = grp.sort_values(x_col)
        plt.plot(grp[x_col], grp[y_col], marker="o", label=str(name))
    plt.title(title)
    plt.xlabel("Year")
    plt.ylabel(ylabel)
    plt.xticks(sorted(df[x_col].unique()))
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()

def save_barh(df, label_col, value_col, title, xlabel, outpath, top_n=15):
    data = df.copy().head(top_n).sort_values(value_col, ascending=True)
    plt.figure(figsize=(10, max(5, 0.38 * len(data))))
    plt.barh(data[label_col].astype(str), data[value_col])
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()

def main() -> None:
    fig_dir = p("outputs/figures")
    ensure_dir(fig_dir)

    forecast_nat = pd.read_csv(p("outputs/forecast/forecast_national_annual.csv")).copy()
    forecast_reg = pd.read_csv(p("outputs/forecast/forecast_top15_regional_def_2030.csv")).copy()

    forecast_nat.columns = [c.strip().lower() for c in forecast_nat.columns]
    forecast_reg.columns = [c.strip().lower() for c in forecast_reg.columns]

    figure_rows = []

    out = fig_dir / "10_forecast_national_diesel_trajectory.png"
    save_line(forecast_nat, "year", "national_diesel_ml", "scenario_name",
              "Forecast 2026-2030: National Diesel Demand", "National diesel (ML)", out)
    figure_rows.append({"figure_file": out.name, "description": "Forecast trajectory of national diesel demand by scenario"})

    out = fig_dir / "11_forecast_central_def_trajectory.png"
    save_line(forecast_nat, "year", "def_central_ml", "scenario_name",
              "Forecast 2026-2030: Central DEF Demand", "Central DEF demand (ML)", out)
    figure_rows.append({"figure_file": out.name, "description": "Forecast trajectory of central DEF demand by scenario"})

    out = fig_dir / "12_forecast_scr_tractor_trajectory.png"
    save_line(forecast_nat, "year", "national_scr_tractor_count", "scenario_name",
              "Forecast 2026-2030: SCR Tractor Count", "Weighted SCR tractor count", out)
    figure_rows.append({"figure_file": out.name, "description": "Forecast trajectory of weighted SCR tractor count by scenario"})

    region_key = "region_key"

    tmp = forecast_reg.loc[forecast_reg["scenario_name"] == "scr_push"].sort_values("regional_def_central_ml", ascending=False).copy()
    out = fig_dir / "13_top15_regional_def_2030_scr_push.png"
    save_barh(tmp, region_key, "regional_def_central_ml",
              "Top 15 Regional DEF Demand in 2030: scr_push",
              "Regional central DEF demand (ML)", out, top_n=15)
    figure_rows.append({"figure_file": out.name, "description": "Top 15 regional central DEF demand in 2030 under scr_push"})

    tmp = forecast_reg.loc[forecast_reg["scenario_name"] == "accelerated_modernization"].sort_values("regional_def_central_ml", ascending=False).copy()
    out = fig_dir / "14_top15_regional_def_2030_accelerated_modernization.png"
    save_barh(tmp, region_key, "regional_def_central_ml",
              "Top 15 Regional DEF Demand in 2030: accelerated_modernization",
              "Regional central DEF demand (ML)", out, top_n=15)
    figure_rows.append({"figure_file": out.name, "description": "Top 15 regional central DEF demand in 2030 under accelerated_modernization"})

    pd.DataFrame(figure_rows).to_csv(p("outputs/figures/forecast_figure_manifest.csv"), index=False)

    print("Forecast figures created:")
    for row in figure_rows:
        print(f"- {row['figure_file']}: {row['description']}")

if __name__ == "__main__":
    main()
