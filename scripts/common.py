from __future__ import annotations
from pathlib import Path
import yaml
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def load_yaml(rel_path: str) -> dict:
    with open(ROOT / rel_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def write_parquet(df: pd.DataFrame, rel_path: str) -> None:
    out = ROOT / rel_path
    ensure_parent(out)
    df.to_parquet(out, index=False)

def write_csv(df: pd.DataFrame, rel_path: str) -> None:
    out = ROOT / rel_path
    ensure_parent(out)
    df.to_csv(out, index=False)

def root_path(rel_path: str) -> Path:
    return ROOT / rel_path
