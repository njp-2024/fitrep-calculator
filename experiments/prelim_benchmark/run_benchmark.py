"""
run_benchmark.py

Entry point for Model Benchmark experiments.

Run from project root with:
  python -m experiments.prelim_benchmark.run_benchmark --prompt-mode uniform   # Part 1
  python -m experiments.prelim_benchmark.run_benchmark --prompt-mode scaled    # Part 2
"""

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import experiments.prelim_benchmark.bench_constants as bench_constants
from experiments.prelim_benchmark.bench_export import save_run
from experiments.prelim_benchmark.bench_loader import load_dataset
from experiments.prelim_benchmark.bench_logger import BenchLogger, BenchResult
from experiments.prelim_benchmark.bench_prompts import (
    base_prompt_builder,
    small_prompt_builder,
    mid_prompt_builder,
)
from src.app.llm_base import BaseLLMClient, LLMRequest
from src.app.llm_clients import OpenAIClient, HuggingFaceClient, LocalModelClient
from src.app.models import ExampleData
import src.app.constants as constants


# Build model registry from bench_constants
MODEL_REGISTRY = []
for name, config in bench_constants.LOCAL_MODELS.items():
    MODEL_REGISTRY.append({
        "name": name,
        "model_id": config["model_id"],
        "size_category": config["size_category"],
        "client_type": "local",
        "reasoning": config.get("reasoning", False),
    })
for name, config in bench_constants.OPEN_WEIGHT_MODELS.items():
    MODEL_REGISTRY.append({
        "name": name,
        "model_id": config["model_id"],
        "size_category": config["size_category"],
        "client_type": "huggingface",
        "reasoning": config.get("reasoning", False),
    })
for name, config in bench_constants.FRONTIER_MODELS.items():
    MODEL_REGISTRY.append({
        "name": name,
        "model_id": config["model_id"],
        "size_category": config["size_category"],
        "client_type": "openai",
        "reasoning": config.get("reasoning", False),
    })


# Prompt builder dispatch map for scaled mode
_SCALED_BUILDERS = {
    bench_constants.MODEL_SIZE_SMALL: ("small", small_prompt_builder),
    bench_constants.MODEL_SIZE_MID:   ("mid",   mid_prompt_builder),
    bench_constants.MODEL_SIZE_LARGE: ("base",  base_prompt_builder),
}


def _get_prompt_builder(prompt_mode: str, size_category: str):
    """
    Return (builder_name, builder_fn) based on prompt mode and model size.

    In 'uniform' mode, all models use base_prompt_builder.
    In 'scaled' mode, the builder is matched to the model's size category.
    """
    if prompt_mode == "uniform":
        return "base", base_prompt_builder

    # scaled mode
    return _SCALED_BUILDERS[size_category]


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for benchmark configuration."""
    parser = argparse.ArgumentParser(
        description="Run model benchmark experiments.",
    )
    parser.add_argument(
        "--prompt-mode",
        type=str,
        choices=["uniform", "scaled"],
        default="uniform",
        help="Prompt strategy: 'uniform' uses base builder for all models, "
             "'scaled' matches builder to model size (default: 'uniform')",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Free-text run description for the manifest",
    )
    parser.add_argument(
        "--skip-local",
        action="store_true",
        default=False,
        help="Skip local (Ollama) models to speed up runs",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        default=False,
        help="Run only local (Ollama) models, skipping API-based models",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="synthetic_cases_v1.json",
        help="Dataset filename in data/ folder (default: synthetic_cases_v1.json)",
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
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + f"_{args.prompt_mode}"
    print(f"Run ID: {run_id}")
    print(f"Prompt mode: {args.prompt_mode}")
    print(f"Dataset file: {args.dataset}")
    print()

    # Load benchmark cases
    dataset = load_dataset(args.dataset)
    print(f"Dataset version: {dataset.version}")
    print(f"Cases loaded: {len(dataset.cases)}")
    print()

    # Load example data (narratives and recommendations) once
    example_data = ExampleData()
    print(f"Example data loaded: {len(example_data.examples)} tiers, "
          f"{len(example_data.recs)} rec categories")
    print()

    # Validate mutually exclusive flags
    if args.skip_local and args.local_only:
        print("ERROR: --skip-local and --local-only are mutually exclusive.")
        return

    # Filter registry by model scope flags
    registry = MODEL_REGISTRY
    if args.skip_local:
        registry = [e for e in registry if e["client_type"] != "local"]
        print("Skipping local models (--skip-local)")
        print()
    elif args.local_only:
        registry = [e for e in registry if e["client_type"] == "local"]
        print("Running local models only (--local-only)")
        print()

    # Initialize clients for each registered model
    print("Initializing model clients...")
    active_clients = []
    skipped = 0

    for entry in registry:
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

        # Resolve prompt builder for this model
        builder_name, builder_fn = _get_prompt_builder(
            args.prompt_mode, entry["size_category"]
        )

        for case in dataset.cases:
            system_prompt, user_prompt = builder_fn(case, example_data)

            # Reasoning models need a higher token budget for chain-of-thought
            max_tokens = (
                bench_constants.MAX_TOKENS_REASONING
                if entry.get("reasoning")
                else bench_constants.MAX_TOKENS
            )

            request = LLMRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=bench_constants.TEMPERATURE,
                reasoning=entry.get("reasoning", False),
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
                    prompt_builder=builder_name,
                    reasoning=entry.get("reasoning", False),
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
                    prompt_builder=builder_name,
                    reasoning=entry.get("reasoning", False),
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
        prompt_mode=args.prompt_mode,
        notes=args.notes,
        model_names=model_names,
        temperature=bench_constants.TEMPERATURE,
        max_tokens=bench_constants.MAX_TOKENS,
        max_tokens_reasoning=bench_constants.MAX_TOKENS_REASONING,
        results=logger.results,
        cases=dataset.cases,
    )
    print(f"Results saved to {run_dir}")
    print(f"Total results: {len(logger.results)}")
    print("Done.")


if __name__ == "__main__":
    main()
