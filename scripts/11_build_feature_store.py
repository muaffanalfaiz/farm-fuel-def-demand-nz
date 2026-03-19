from __future__ import annotations
import pandas as pd
from pathlib import Path
from scripts.common import root_path, write_csv, write_parquet

def safe_read_csv(path: Path):
    if path.exists():
        return pd.read_csv(path)
    return None

def main() -> None:
    master = pd.read_csv(root_path("outputs/tables/regional_master_table.csv")).copy()
    master.columns = [c.strip().lower() for c in master.columns]

    # Optional external joins. These files may not exist yet.
    optional_files = {
        "agri_production": root_path("data/raw/agriculture/agri_production_region_farmtype.csv"),
        "farm_numbers": root_path("data/raw/agriculture/farm_numbers_region.csv"),
        "farm_size": root_path("data/raw/agriculture/farm_size_region.csv"),
        "registrations": root_path("data/raw/nzta_registrations/tractor_registrations_monthly.csv"),
    }

    join_notes = []

    for label, path in optional_files.items():
        df = safe_read_csv(path)
        if df is None:
            join_notes.append({"dataset": label, "status": "missing", "path": str(path)})
            continue

        df.columns = [c.strip().lower() for c in df.columns]

        # very simple region-key harmonization placeholder
        possible_keys = ["region_key", "tla", "region", "territorial_authority", "postcode"]
        found = [c for c in possible_keys if c in df.columns]
        if not found:
            join_notes.append({"dataset": label, "status": "no_join_key", "path": str(path)})
            continue

        join_key = found[0]
        if join_key != "region_key":
            df = df.rename(columns={join_key: "region_key"})

        # avoid duplicate columns
        keep_cols = ["region_key"] + [c for c in df.columns if c != "region_key" and c not in master.columns]
        df = df[keep_cols].copy()

        master = master.merge(df, on="region_key", how="left")
        join_notes.append({"dataset": label, "status": "joined", "path": str(path)})

    # Core engineered features that are valid even without external joins
    master["diesel_per_active_tractor_l"] = master["regional_diesel_litres"] / master["regional_active_licensed_count"]
    master["scr_share_of_regional_diesel"] = master["regional_scr_diesel_litres"] / master["regional_diesel_litres"]
    master["def_central_per_active_tractor_l"] = (master["regional_def_central_ml"] * 1_000_000) / master["regional_active_licensed_count"]

    # Rank variables
    master["rank_diesel"] = master["regional_diesel_litres"].rank(method="dense", ascending=False)
    master["rank_def_central"] = master["regional_def_central_ml"].rank(method="dense", ascending=False)
    master["rank_active_fleet"] = master["regional_active_licensed_count"].rank(method="dense", ascending=False)

    write_csv(master, "outputs/tables/regional_feature_store.csv")
    write_parquet(master, "data/marts/regional_feature_store.parquet")
    write_csv(pd.DataFrame(join_notes), "outputs/tables/feature_store_join_log.csv")

    print("Regional feature store created.")
    print(master.head(15).to_string(index=False))
    print("\nJoin log:")
    print(pd.DataFrame(join_notes).to_string(index=False))

if __name__ == "__main__":
    main()
