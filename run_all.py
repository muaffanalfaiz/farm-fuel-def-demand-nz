"""
Canonical pipeline runner for farm-fuel-def-demand-nz.

Usage:
    python run_all.py           # run the full pipeline
    python run_all.py --from 14 # resume from script 14 onwards
"""
from __future__ import annotations
import subprocess
import sys
import argparse

PIPELINE = [
    "scripts/00_build_internal_files_from_report_extract.py",
    "scripts/01_download_data.py",
    "scripts/02_prepare_internal_tables.py",
    "scripts/03_parse_nzta_fleet.py",
    "scripts/05_assign_tiers.py",
    "scripts/06_estimate_diesel.py",
    "scripts/07_estimate_def.py",
    "scripts/08_build_summary.py",
    "scripts/09_validate_outputs.py",
    "scripts/10_build_regional_master_table.py",
    "scripts/11_build_feature_store.py",
    "scripts/12_geography_qa.py",
    "scripts/13_prepare_external_templates.py",
    "scripts/14_run_scenarios.py",
    "scripts/15_scenario_summary.py",
    "scripts/16_export_dashboard.py",
    "scripts/17_make_figures.py",
    "scripts/18_write_narratives.py",
    "scripts/19_pack_release.py",
    "scripts/20_run_forecast.py",
    "scripts/21_make_forecast_figures.py",
    "scripts/22_write_prediction_note.py",
]


def extract_number(path: str) -> int:
    """Extract the leading number from a script filename."""
    name = path.split("/")[-1]
    return int(name.split("_")[0])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the canonical pipeline.")
    parser.add_argument(
        "--from", dest="start_from", type=int, default=0,
        help="Script number to start from (e.g. --from 14)"
    )
    args = parser.parse_args()

    scripts = PIPELINE
    if args.start_from > 0:
        scripts = [s for s in scripts if extract_number(s) >= args.start_from]

    if not scripts:
        print("No scripts matched the --from filter.")
        return

    print(f"Running {len(scripts)} scripts...")
    print()

    for script in scripts:
        num = extract_number(script)
        name = script.split("/")[-1]
        print(f"{'='*60}")
        print(f"  [{num:02d}] {name}")
        print(f"{'='*60}")

        result = subprocess.run(
            [sys.executable, "-m", "scripts." + name.replace(".py", "")],
            capture_output=False,
        )
        if result.returncode != 0:
            print(f"\n*** FAILED at {name} (exit code {result.returncode}) ***")
            print(f"Fix the issue, then resume with:  python run_all.py --from {num}")
            sys.exit(result.returncode)

        print()

    print("="*60)
    print("  Pipeline complete.")
    print("="*60)


if __name__ == "__main__":
    main()
