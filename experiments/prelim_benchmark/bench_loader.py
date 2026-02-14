"""
Loads benchmark case data from /data for use in the experiment.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from experiments.prelim_benchmark.bench_constants import ALLOWED_TIERS


@dataclass
class BenchCase:
    case_id: str
    rank: str
    name: str
    billet_title: str
    accomplishments: list[str]
    context: str
    target_tier: str


@dataclass
class BenchDataset:
    version: str
    description: str
    allowed_tiers: list[str]
    cases: list[BenchCase]


def load_dataset() -> BenchDataset:
    """Load and validate the synthetic benchmark cases from JSON."""
    data_path = Path(__file__).parent / "data" / "synthetic_cases_v1.json"

    with open(data_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Validate top-level structure
    if "metadata" not in raw:
        raise ValueError("Dataset missing 'metadata' key")
    if "cases" not in raw:
        raise ValueError("Dataset missing 'cases' key")

    metadata = raw["metadata"]

    # Build cases and validate tiers
    cases = []
    for entry in raw["cases"]:
        tier = entry["target_tier"]
        if tier not in ALLOWED_TIERS:
            raise ValueError(
                f"Case {entry.get('case_id', '?')}: "
                f"target_tier '{tier}' not in {ALLOWED_TIERS}"
            )
        cases.append(BenchCase(
            case_id=entry["case_id"],
            rank=entry["rank"],
            name=entry["name"],
            billet_title=entry["billet_title"],
            accomplishments=entry["accomplishments"],
            context=entry["context"],
            target_tier=tier,
        ))

    return BenchDataset(
        version=metadata["version"],
        description=metadata["description"],
        allowed_tiers=metadata["allowed_tiers"],
        cases=cases,
    )
