from __future__ import annotations
import pandas as pd
from scripts.common import root_path, write_parquet

def main() -> None:
    fleet = pd.read_parquet(root_path("data/marts/fleet_diesel_estimates.parquet"))

    # Replace this with joined regional agriculture features once downloaded.
    features = (
        fleet.groupby("territorial_authority", dropna=False)
        .agg(
            tractor_stock=("tier_assigned", "size"),
            diesel_litres=("annual_diesel_litres", "sum"),
            median_vehicle_year=("vehicle_year", "median"),
        )
        .reset_index()
    )
    features["median_age_proxy"] = 2025 - features["median_vehicle_year"].fillna(2025)

    tier_mix = (
        fleet.pivot_table(
            index="territorial_authority",
            columns="tier_assigned",
            values="annual_diesel_litres",
            aggfunc="size",
            fill_value=0
        )
        .reset_index()
    )

    mart = features.merge(tier_mix, on="territorial_authority", how="left")
    write_parquet(mart, "data/marts/feature_store_region.parquet")
    print("Built regional feature store.")

if __name__ == "__main__":
    main()
