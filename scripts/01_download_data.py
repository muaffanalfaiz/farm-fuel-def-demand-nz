from __future__ import annotations
import requests
from pathlib import Path
from scripts.common import load_yaml, root_path

cfg = load_yaml("config/paths.yaml")
downloads = cfg["downloads"]

def download(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    out_path.write_bytes(r.content)
    print(f"Downloaded: {out_path}")

def main() -> None:
    download(downloads["nzta_fleet_all_years"], root_path("data/raw/nzta/Fleet-data-all-vehicle-years.zip"))
    download(downloads["nzta_data_dictionary"], root_path("data/raw/nzta/MVROpenData-Dictionary.csv"))
    download(downloads["dairynz_pdf_2023_24"], root_path("data/raw/dairynz/dairy-statistics-2023-24.pdf"))
    # Optional example Beef+Lamb spreadsheet:
    try:
        download(downloads["beeflamb_example_class3_nni"], root_path("data/raw/beeflamb/northern-north-island-class-3-hard-hill-country.xlsx"))
    except Exception as e:
        print(f"Optional Beef+Lamb example failed: {e}")
    print("\nManual downloads still needed:")
    for k, v in cfg["manual_sources"].items():
        print(f"- {k}: {v}")

if __name__ == "__main__":
    main()
