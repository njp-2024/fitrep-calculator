"""
bench_logger.py

Dataclass and logger for capturing benchmark results.
Each BenchResult records one case-model pair; BenchLogger
collects results and writes them to a single JSON file per run.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class BenchResult:
    """One generation result for a single case-model pair."""
    run_id: str
    case_id: str
    model_name: str           # display name (e.g. "GPT-4o-mini")
    model_id: str             # API ID (e.g. "gpt-4o-mini")
    client_type: str          # "openai" | "huggingface" | "local"
    target_tier: str
    generated_text: str
    char_count: int
    prompt_tokens: int | None
    completion_tokens: int | None
    latency_sec: float
    error: str | None         # None if success, error message if failed
    prompt_builder: str       # which builder was used (e.g. "base", "small", "mid")


class BenchLogger:
    """
    Collects BenchResult entries during a run and writes them
    to a single JSON file when save() is called.
    """

    def __init__(self, run_id: str, dataset_version: str):
        self.run_id = run_id
        self.dataset_version = dataset_version
        self.results: list[BenchResult] = []

    def log(self, result: BenchResult):
        """Append a result and print a one-line summary to the console."""
        self.results.append(result)

        if result.error:
            status = f"ERROR: {result.error[:60]}"
        else:
            status = f"{result.char_count} chars"

        count = len(self.results)
        print(f"  [{count}] {result.model_name} | {result.case_id} "
              f"| {result.latency_sec:.1f}s | {status}")

    def save(self, output_dir: Path):
        """
        Write all results to a JSON file named {run_id}.json.

        Note: For structured per-run output (manifest, results, survey CSV),
        use bench_export.save_run() instead.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"{self.run_id}.json"

        payload = {
            "run_id": self.run_id,
            "dataset_version": self.dataset_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_results": len(self.results),
            "results": [asdict(r) for r in self.results],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        return filepath
