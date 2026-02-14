"""
run_benchmark.py

Entry point for Model Benchmark experiments.

Run from project root with:
  python -m experiments.prelim_benchmark.run_benchmark
  python -m experiments.prelim_benchmark.run_benchmark --prompt-variant base --notes "baseline run"
"""

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import experiments.prelim_benchmark.bench_constants as bench_constants
from experiments.prelim_benchmark.bench_export import save_run
from experiments.prelim_benchmark.bench_loader import load_dataset
from experiments.prelim_benchmark.bench_logger import BenchLogger, BenchResult
from experiments.prelim_benchmark.bench_prompts import base_prompt_builder
from src.app.llm_base import BaseLLMClient, LLMRequest
from src.app.llm_clients import OpenAIClient, HuggingFaceClient, LocalModelClient
from src.app.models import ExampleData
import src.app.constants as constants


# Build model registry from bench_constants
MODEL_REGISTRY = []
for name, model_id in bench_constants.LOCAL_MODELS.items():
    MODEL_REGISTRY.append({"name": name, "model_id": model_id, "client_type": "local"})
for name, model_id in bench_constants.OPEN_WEIGHT_MODELS.items():
    MODEL_REGISTRY.append({"name": name, "model_id": model_id, "client_type": "huggingface"})
for name, model_id in bench_constants.FRONTIER_MODELS.items():
    MODEL_REGISTRY.append({"name": name, "model_id": model_id, "client_type": "openai"})


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for benchmark configuration."""
    parser = argparse.ArgumentParser(
        description="Run model benchmark experiments.",
    )
    parser.add_argument(
        "--prompt-variant",
        type=str,
        default="base",
        help="Which prompt builder was used (default: 'base')",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Free-text run description for the manifest",
    )
    return parser.parse_args()


def _init_client(entry: dict) -> BaseLLMClient | None:
    """
    Attempt to initialize an LLM client for a registry entry.
    Returns None if the client cannot be created (missing key, no ollama, etc).
    """
    client_type = entry["client_type"]
    model_id = entry["model_id"]

    try:
        if client_type == "local":
            return LocalModelClient(local_path=constants.OLLAMA_PATH, model=model_id)
        elif client_type == "huggingface":
            return HuggingFaceClient(model=model_id)
        elif client_type == "openai":
            return OpenAIClient(model=model_id)
        else:
            print(f"  WARNING: Unknown client type '{client_type}' for {entry['name']}")
            return None
    except (ValueError, RuntimeError) as e:
        print(f"  WARNING: Skipping {entry['name']} — {e}")
        return None


def main():
    args = _parse_args()

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

    # Initialize clients for each registered model
    print("Initializing model clients...")
    active_clients = []
    skipped = 0

    for entry in MODEL_REGISTRY:
        client = _init_client(entry)
        if client is not None:
            active_clients.append({"entry": entry, "client": client})
            print(f"  OK: {entry['name']} ({entry['client_type']})")
        else:
            skipped += 1

    print()
    print(f"Active models: {len(active_clients)} | Skipped: {skipped}")
    print()

    if not active_clients:
        print("No models available. Exiting.")
        return

    # Set up logger
    logger = BenchLogger(run_id=run_id, dataset_version=dataset.version)

    # Generation loop — outer: models, inner: cases
    total_pairs = len(active_clients) * len(dataset.cases)
    print(f"Starting generation loop ({total_pairs} total pairs)...")
    print()

    for model_info in active_clients:
        entry = model_info["entry"]
        client = model_info["client"]
        print(f"--- {entry['name']} ({entry['model_id']}) ---")

        for case in dataset.cases:
            system_prompt, user_prompt = base_prompt_builder(case, example_data)

            request = LLMRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=bench_constants.MAX_TOKENS,
                temperature=bench_constants.TEMPERATURE,
            )

            start = time.time()
            try:
                response = client.generate(request)
                elapsed = time.time() - start

                result = BenchResult(
                    run_id=run_id,
                    case_id=case.case_id,
                    model_name=entry["name"],
                    model_id=entry["model_id"],
                    client_type=entry["client_type"],
                    target_tier=case.target_tier,
                    generated_text=response.text,
                    char_count=len(response.text),
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                    latency_sec=round(elapsed, 2),
                    error=None,
                )
            except RuntimeError as e:
                elapsed = time.time() - start

                result = BenchResult(
                    run_id=run_id,
                    case_id=case.case_id,
                    model_name=entry["name"],
                    model_id=entry["model_id"],
                    client_type=entry["client_type"],
                    target_tier=case.target_tier,
                    generated_text="",
                    char_count=0,
                    prompt_tokens=None,
                    completion_tokens=None,
                    latency_sec=round(elapsed, 2),
                    error=str(e),
                )

            logger.log(result)

        print()

    # Save structured run output
    output_dir = Path(__file__).parent / "outputs"
    model_names = [m["entry"]["name"] for m in active_clients]
    run_dir = save_run(
        base_output_dir=output_dir,
        run_id=run_id,
        dataset_version=dataset.version,
        prompt_variant=args.prompt_variant,
        notes=args.notes,
        model_names=model_names,
        temperature=bench_constants.TEMPERATURE,
        max_tokens=bench_constants.MAX_TOKENS,
        results=logger.results,
        cases=dataset.cases,
    )
    print(f"Results saved to {run_dir}")
    print(f"Total results: {len(logger.results)}")
    print("Done.")


if __name__ == "__main__":
    main()
