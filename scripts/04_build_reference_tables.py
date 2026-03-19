from __future__ import annotations
import pandas as pd
from scripts.common import root_path, write_csv

def build_ta_region_lookup() -> pd.DataFrame:
    # Fill this from Stats NZ / LINZ / your preferred official lookup.
    data = [
        {"territorial_authority": "Auckland", "region": "Auckland"},
        {"territorial_authority": "Waikato", "region": "Waikato"},
        {"territorial_authority": "Canterbury", "region": "Canterbury"},
        {"territorial_authority": "Southland", "region": "Southland"},
    ]
    return pd.DataFrame(data)

def main() -> None:
    ta = build_ta_region_lookup()
    write_csv(ta, "data/reference/ta_region_lookup.csv")
    print("Wrote TA-region lookup starter file. Expand it before production.")

if __name__ == "__main__":
    main()
