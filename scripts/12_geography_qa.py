from __future__ import annotations
import pandas as pd
from scripts.common import root_path, write_csv

URBAN_HINTS = [
    "CITY", "AUCKLAND", "CHRISTCHURCH", "HAMILTON", "PALMERSTON NORTH",
    "INVERCARGILL", "WELLINGTON", "DUNEDIN", "TAURANGA", "WHANGAREI",
    "LOWER HUTT", "UPPER HUTT", "PORIRUA", "NELSON"
]

def main() -> None:
    master = pd.read_csv(root_path("outputs/tables/regional_master_table.csv")).copy()
    summary = pd.read_csv(root_path("outputs/tables/project_summary.csv")).copy()

    master.columns = [c.strip().lower() for c in master.columns]
    summary.columns = [c.strip().lower() for c in summary.columns]

    # Make region_key safe and explicit
    master["region_key"] = master["region_key"].fillna("MISSING_REGION").astype(str).str.strip()
    master["region_key_upper"] = master["region_key"].str.upper()

    national_fleet = float(summary.loc[0, "project_active_licensed_weighted_fleet"])
    national_diesel_ml = float(summary.loc[0, "project_national_diesel_ml"])
    national_def_central_ml = float(summary.loc[0, "def_central_ml"])

    master["fleet_share_pct"] = master["share_of_national_fleet"] * 100
    master["diesel_share_pct"] = master["share_of_national_diesel"] * 100
    master["def_share_pct"] = master["share_of_national_def_central"] * 100

    master["fleet_to_diesel_share_ratio"] = master["share_of_national_fleet"] / master["share_of_national_diesel"]
    master["def_to_diesel_share_ratio"] = master["share_of_national_def_central"] / master["share_of_national_diesel"]

    master["is_urban_hint"] = master["region_key_upper"].apply(
        lambda x: any(h in x for h in URBAN_HINTS)
    )

    master["admin_bias_flag"] = (
        (master["fleet_to_diesel_share_ratio"] >= 1.5)
        | ((master["is_urban_hint"]) & (master["share_of_national_fleet"] >= 0.02))
    )

    top_diesel = master.sort_values("regional_diesel_litres", ascending=False).copy()
    top_fleet = master.sort_values("regional_active_licensed_count", ascending=False).copy()
    flagged = master.loc[master["admin_bias_flag"]].sort_values(
        ["fleet_to_diesel_share_ratio", "regional_diesel_litres"], ascending=[False, False]
    ).copy()

    missing_key_count = int((master["region_key"] == "MISSING_REGION").sum())

    qa_summary = pd.DataFrame([{
        "national_fleet_weighted": national_fleet,
        "national_diesel_ml": national_diesel_ml,
        "national_def_central_ml": national_def_central_ml,
        "region_count": int(master["region_key"].nunique()),
        "urban_hint_count": int(master["is_urban_hint"].sum()),
        "admin_bias_flag_count": int(master["admin_bias_flag"].sum()),
        "missing_region_key_count": missing_key_count,
        "top_region_by_diesel": str(top_diesel.iloc[0]["region_key"]),
        "top_region_by_fleet": str(top_fleet.iloc[0]["region_key"]),
        "top_region_by_def": str(master.sort_values("regional_def_central_ml", ascending=False).iloc[0]["region_key"])
    }])

    write_csv(qa_summary, "outputs/tables/geography_qa_summary.csv")
    write_csv(top_diesel, "outputs/tables/geography_qa_top_diesel.csv")
    write_csv(top_fleet, "outputs/tables/geography_qa_top_fleet.csv")
    write_csv(flagged, "outputs/tables/geography_qa_flags.csv")

    print("Geography QA summary:")
    print(qa_summary.to_string(index=False))

    print("\nTop 15 by diesel:")
    print(
        top_diesel[[
            "region_key", "regional_diesel_ml", "regional_def_central_ml",
            "fleet_share_pct", "diesel_share_pct", "fleet_to_diesel_share_ratio", "is_urban_hint"
        ]].head(15).to_string(index=False)
    )

    print("\nFlagged possible administrative / registration-bias regions:")
    if len(flagged) == 0:
        print("No flagged regions.")
    else:
        print(
            flagged[[
                "region_key", "regional_diesel_ml", "regional_def_central_ml",
                "fleet_share_pct", "diesel_share_pct", "fleet_to_diesel_share_ratio", "is_urban_hint"
            ]].head(25).to_string(index=False)
        )

if __name__ == "__main__":
    main()
