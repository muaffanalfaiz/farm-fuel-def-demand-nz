from __future__ import annotations
import pandas as pd
from pathlib import Path
from scripts.common import root_path, write_csv

def main() -> None:
    master = pd.read_csv(root_path("outputs/tables/regional_master_table.csv")).copy()
    master.columns = [c.strip().lower() for c in master.columns]

    region_ref = master[["region_key"]].drop_duplicates().sort_values("region_key").copy()
    region_ref["notes"] = ""
    write_csv(region_ref, "outputs/tables/region_key_reference.csv")

    template_dir = root_path("data/raw/templates")
    template_dir.mkdir(parents=True, exist_ok=True)

    agri_template = region_ref.copy()
    agri_template["farm_type"] = ""
    agri_template["agri_area_ha"] = ""
    agri_template["agri_output_value"] = ""
    agri_template["source_note"] = ""
    agri_template.to_csv(template_dir / "template_agri_production_region_farmtype.csv", index=False)

    farm_numbers_template = region_ref.copy()
    farm_numbers_template["farm_count"] = ""
    farm_numbers_template["source_note"] = ""
    farm_numbers_template.to_csv(template_dir / "template_farm_numbers_region.csv", index=False)

    farm_size_template = region_ref.copy()
    farm_size_template["avg_farm_size_ha"] = ""
    farm_size_template["median_farm_size_ha"] = ""
    farm_size_template["source_note"] = ""
    farm_size_template.to_csv(template_dir / "template_farm_size_region.csv", index=False)

    print("Created:")
    print("- outputs/tables/region_key_reference.csv")
    print("- data/raw/templates/template_agri_production_region_farmtype.csv")
    print("- data/raw/templates/template_farm_numbers_region.csv")
    print("- data/raw/templates/template_farm_size_region.csv")

if __name__ == "__main__":
    main()
