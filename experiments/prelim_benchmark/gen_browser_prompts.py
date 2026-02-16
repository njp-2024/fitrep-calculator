"""
Generates copy-paste prompts for frontier model browser testing.

Renders all cases from the synthetic dataset into a single .txt file
formatted for manual copy-paste into browser-based LLMs (e.g. ChatGPT, Claude).
System and user prompts are combined into a single block per case since
browser interfaces don't expose separate system prompt fields.

Usage:
    python -m experiments.prelim_benchmark.gen_browser_prompts
"""

import random
from pathlib import Path

from experiments.prelim_benchmark.bench_loader import load_dataset
from experiments.prelim_benchmark.bench_prompts import base_prompt_builder
from src.app.models import ExampleData

# Reproducibility
RANDOM_SEED = 42
DATA_FILE = "synthetic_cases_TIERED.json"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "browser_prompts.txt"

SEPARATOR = "=" * 80


def main():
    """Load cases, build prompts, and write output file."""
    random.seed(RANDOM_SEED)
    dataset = load_dataset(DATA_FILE)
    example_data = ExampleData()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    lines = []
    for case in dataset.cases:
        system_prompt, user_prompt = base_prompt_builder(case, example_data)

        lines.append(SEPARATOR)
        lines.append(f"CASE: {case.case_id} | TIER: {case.target_tier}")
        lines.append(SEPARATOR)
        lines.append("")
        lines.append("[SYSTEM INSTRUCTIONS]")
        lines.append(system_prompt)
        lines.append("")
        lines.append("[USER REQUEST]")
        lines.append(user_prompt)
        lines.append("")
        lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {len(dataset.cases)} prompt blocks to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
