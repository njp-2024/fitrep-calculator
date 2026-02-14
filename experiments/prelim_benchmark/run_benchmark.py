"""
run_benchmark.py

Entry point for Model Benchmark experiments.

Run from project root with: python -m experiments.prelim_benchmark.run_benchmark
"""

from datetime import datetime, timezone

from experiments.prelim_benchmark.bench_loader import load_dataset


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

    # Print summary of each case
    for case in dataset.cases:
        print(f"  {case.case_id} | {case.rank} {case.name} | {case.target_tier}")

    print()
    print("Benchmark harness initialized successfully.")


if __name__ == "__main__":
    main()
