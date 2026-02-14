"""
bench_export.py

Structured output writers for benchmark runs.
Creates per-run subfolders with manifest, results, and blinded survey CSV.

For simple flat-file output, see BenchLogger.save() in bench_logger.py.
"""

import csv
import json
import random
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from experiments.prelim_benchmark.bench_loader import BenchCase
from experiments.prelim_benchmark.bench_logger import BenchResult


def save_run(
    base_output_dir: Path,
    run_id: str,
    dataset_version: str,
    prompt_variant: str,
    notes: str,
    model_names: list[str],
    temperature: float,
    max_tokens: int,
    results: list[BenchResult],
    cases: list[BenchCase],
) -> Path:
    """
    Top-level entry point for structured run output.
    Creates outputs/runs/{run_id}/ with manifest.json, results.json, and survey.csv.
    Returns the run directory path.
    """
    run_dir = base_output_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    write_manifest(
        run_dir, run_id, dataset_version, prompt_variant,
        notes, model_names, temperature, max_tokens,
    )
    write_results(run_dir, run_id, dataset_version, results)
    write_survey_csv(run_dir, results, cases)

    return run_dir


def write_manifest(
    run_dir: Path,
    run_id: str,
    dataset_version: str,
    prompt_variant: str,
    notes: str,
    model_names: list[str],
    temperature: float,
    max_tokens: int,
) -> Path:
    """Write manifest.json with run metadata and generation parameters."""
    filepath = run_dir / "manifest.json"

    payload = {
        "run_id": run_id,
        "dataset_version": dataset_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_variant": prompt_variant,
        "notes": notes,
        "models": model_names,
        "generation_params": {
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return filepath


def write_results(
    run_dir: Path,
    run_id: str,
    dataset_version: str,
    results: list[BenchResult],
) -> Path:
    """Write results.json — same schema as the flat-file logger output."""
    filepath = run_dir / "results.json"

    payload = {
        "run_id": run_id,
        "dataset_version": dataset_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_results": len(results),
        "results": [asdict(r) for r in results],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return filepath


def write_survey_csv(
    run_dir: Path,
    results: list[BenchResult],
    cases: list[BenchCase],
) -> Path:
    """
    Write survey.csv — blinded and shuffled rows for human evaluation.
    No model identity is included; rows are randomized to prevent ordering bias.
    Case data (rank, name, billet, accomplishments) is joined via case_id.
    """
    filepath = run_dir / "survey.csv"

    # Build case lookup
    case_lookup = {c.case_id: c for c in cases}

    # Build rows from successful results only
    rows = []
    for result in results:
        if result.error is not None:
            continue

        case = case_lookup.get(result.case_id)
        if case is None:
            continue

        rows.append({
            "evaluation_id": uuid.uuid4().hex[:8],
            "rank": case.rank,
            "name": case.name,
            "billet": case.billet_title,
            "accomplishments": "\n".join(case.accomplishments),
            "target_tier": result.target_tier,
            "narrative": result.generated_text,
        })

    # Shuffle for blinding
    random.shuffle(rows)

    fieldnames = [
        "evaluation_id", "rank", "name", "billet",
        "accomplishments", "target_tier", "narrative",
    ]

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return filepath
