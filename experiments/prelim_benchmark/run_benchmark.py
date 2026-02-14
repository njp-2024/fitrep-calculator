"""
run_benchmark.py

Entry point for Model Benchmark experiments.

Run from project root with: python -m experiments.prelim_benchmark.run_benchmark
"""

from datetime import datetime, timezone

from experiments.prelim_benchmark.bench_loader import load_dataset
from experiments.prelim_benchmark.bench_prompts import base_prompt_builder
from src.app.models import ExampleData


def main():
    print("=== Model Benchmark Runner ===")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"Run ID: {run_id}")
    print()

    # Load benchmark cases
    dataset = load_dataset()
    print(f"Dataset version: {dataset.version}")
    print(f"Cases loaded: {len(dataset.cases)}")
    print()

    # Load example data (narratives and recommendations) once
    example_data = ExampleData()
    print(f"Example data loaded: {len(example_data.examples)} tiers, "
          f"{len(example_data.recs)} rec categories")
    print()

    # Build and preview prompts for each case
    for case in dataset.cases:
        system_prompt, user_prompt = base_prompt_builder(case, example_data)
        preview = user_prompt[:200].replace("\n", " ")

        print(f"  {case.case_id} | {case.rank} {case.name} | {case.target_tier}")
        print(f"    System prompt: {len(system_prompt)} chars")
        print(f"    User prompt:   {len(user_prompt)} chars")
        print(f"    Preview: {preview}...")
        print()

    print("Benchmark harness initialized successfully.")


if __name__ == "__main__":
    main()
