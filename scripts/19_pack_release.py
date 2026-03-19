from __future__ import annotations
import shutil
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def p(rel: str) -> Path:
    return ROOT / rel

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def copy_file(src: Path, dst: Path, manifest_rows: list[dict]) -> None:
    if src.exists():
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        manifest_rows.append({"source": str(src.relative_to(ROOT)), "destination": str(dst.relative_to(ROOT)), "status": "copied"})
    else:
        manifest_rows.append({"source": str(src.relative_to(ROOT)), "destination": str(dst.relative_to(ROOT)), "status": "missing"})

def main() -> None:
    release_dir = p("release/package_contents")
    if release_dir.exists():
        shutil.rmtree(release_dir)
    ensure_dir(release_dir)

    manifest_rows = []

    files_to_copy = [
        "outputs/tables/project_summary.csv",
        "outputs/tables/validation_checks.csv",
        "outputs/tables/national_diesel_by_tier.csv",
        "outputs/tables/regional_master_table.csv",
        "outputs/tables/regional_feature_store.csv",
        "outputs/tables/geography_qa_summary.csv",
        "outputs/tables/geography_qa_flags.csv",
        "outputs/scenarios/scenario_national_summary.csv",
        "outputs/scenarios/scenario_national_compare.csv",
        "outputs/scenarios/scenario_national_by_tier.csv",
        "outputs/scenarios/scenario_regional_summary.csv",
        "outputs/scenarios/scenario_regional_compare.csv",
        "outputs/scenarios/scenario_top_regional_def_gains.csv",
        "outputs/forecast/forecast_national_annual.csv",
        "outputs/forecast/forecast_national_by_tier_annual.csv",
        "outputs/forecast/forecast_regional_annual.csv",
        "outputs/forecast/forecast_top15_regional_def_2030.csv",
        "outputs/figures/figure_manifest.csv",
        "outputs/figures/forecast_figure_manifest.csv",
        "docs/01_methods_summary.md",
        "docs/02_key_findings.md",
        "docs/03_limitations.md",
        "docs/04_github_readme_draft.md",
        "docs/05_results_snapshot.md",
        "docs/06_prediction_note.md",
    ]

    for rel in files_to_copy:
        copy_file(p(rel), release_dir / rel, manifest_rows)

    fig_dir = p("outputs/figures")
    if fig_dir.exists():
        for fig in sorted(fig_dir.glob("*.png")):
            copy_file(fig, release_dir / "outputs/figures" / fig.name, manifest_rows)

    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(p("release/release_manifest.csv"), index=False)

    archive_base = p("release/farm-fuel-def-demand-nz_release")
    zip_path = p("release/farm-fuel-def-demand-nz_release.zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(archive_base), "zip", root_dir=release_dir)

    print("Release package refreshed:")
    print("- release/package_contents/")
    print("- release/release_manifest.csv")
    print("- release/farm-fuel-def-demand-nz_release.zip")

if __name__ == "__main__":
    main()
