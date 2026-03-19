from __future__ import annotations
import zipfile
import pandas as pd
from pathlib import Path
from scripts.common import root_path, write_parquet, write_csv

ZIP_PATH = root_path("data/raw/nzta/Fleet-data-all-vehicle-years.zip")

def read_zipped_csv(zip_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path, "r") as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise FileNotFoundError("No CSV found inside NZTA zip")
        with zf.open(csv_names[0]) as f:
            df = pd.read_csv(f, low_memory=False)
    return df

def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [c.strip().lower() for c in out.columns]
    return out

def filter_tractors(df: pd.DataFrame) -> pd.DataFrame:
    possible_fields = [c for c in df.columns if c in {"class", "body_type", "model", "sub_model", "vehicle_type", "description"}]
    if not possible_fields:
        return df.copy()

    mask = pd.Series(False, index=df.index)
    for c in possible_fields:
        mask = mask | df[c].astype(str).str.lower().str.contains("tractor", na=False)

    return df.loc[mask].copy()

def main() -> None:
    df = read_zipped_csv(ZIP_PATH)
    df = normalise_columns(df)
    tractors = filter_tractors(df)

    geo_candidates = [
        c for c in tractors.columns
        if (
            "territ" in c.lower()
            or "author" in c.lower()
            or "region" in c.lower()
            or "district" in c.lower()
            or c.lower() in {"ta"}
        )
    ]

    write_parquet(df, "data/staging/nzta_fleet_all.parquet")
    write_parquet(tractors, "data/staging/nzta_tractors.parquet")
    write_csv(tractors.head(1000), "data/exports/nzta_tractors_sample.csv")

    print(f"All rows: {len(df):,}")
    print(f"Tractor rows: {len(tractors):,}")
    print(f"Total columns in full fleet: {len(df.columns)}")
    print("Geography candidate columns:", geo_candidates)
    print("First 50 columns:", df.columns[:50].tolist())

if __name__ == "__main__":
    main()
