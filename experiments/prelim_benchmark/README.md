# Preliminary Model Benchmark

This directory contains the experimental framework for evaluating LLM capability on structured narrative generation tasks (fitrep Section I narratives).

This harness is **separate from the production app** and is used exclusively for controlled capability screening and internal experimentation.

---

## Current Status

The benchmark harness is functional and can execute end-to-end runs across multiple models.

Implemented:

- Experiment entry point with CLI args (`run_benchmark.py`)
- Synthetic dataset loading and validation (`bench_loader.py`)
- Multi-model execution loop (local, HuggingFace, OpenAI clients)
- Prompt builders for benchmark use (`bench_prompts.py`): base, small, and mid builders
- Per-result logging with console summaries (`bench_logger.py`)
- Structured per-run output with manifest, results, and survey CSV (`bench_export.py`)
- Blinded, randomized CSV export for human evaluation via surveys
- Part 2 scaled prompts per model size (`--prompt-mode scaled`)

Not yet implemented:

- Aggregate metrics reporting
- Automated summary generation

---

## Purpose

This study is a rapid, exploratory capability screening designed to inform AI deployment strategy for structured performance narrative generation tasks. There are two parts:

1. **Part 1** -- One standard prompt, same across all models. Isolates raw model capability.
2. **Part 2** -- Lightly scaled prompts per model size. Tests whether simple prompt scaling closes any gaps.

Human evaluators will assess generated narratives via blinded surveys built from the CSV export.

---

## Directory Structure

```
prelim_benchmark/
├── run_benchmark.py        # Entry point for benchmark runs
├── bench_constants.py      # Model registries, allowed tiers
├── bench_export.py         # Structured output writers (manifest, results, survey CSV)
├── bench_loader.py         # Synthetic dataset loader
├── bench_logger.py         # BenchResult dataclass and run logger
├── bench_prompts.py        # Prompt builders for benchmark use
├── data/
│   └── synthetic_cases_v1.json
├── config/
└── outputs/
    └── runs/
        └── {run_id}/
            ├── manifest.json   # Run metadata, models, generation params
            ├── results.json    # Full BenchResult data
            └── survey.csv      # Blinded, shuffled rows for human evaluation
```

---

## Running a Benchmark

From the project root:

```bash
python -m experiments.prelim_benchmark.run_benchmark
```

With optional arguments:

```bash
python -m experiments.prelim_benchmark.run_benchmark --prompt-mode uniform --notes "Part 1 baseline run"
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--prompt-mode` | `"uniform"` | Prompt strategy: `uniform` uses base builder for all models, `scaled` matches builder to model size |
| `--notes` | `""` | Free-text run description saved to manifest |
| `--skip-local` | off | Exclude local models from the run |

---

## Output Files

Each run creates `outputs/runs/{run_id}/` containing:

- **manifest.json** -- Run metadata: prompt mode, notes, model list, temperature, max_tokens
- **results.json** -- Full generation results (text, token counts, latency, errors)
- **survey.csv** -- Blinded and shuffled rows for building human evaluation surveys. Contains case context and generated narrative but no model identity.

---

## Notes

- The experiment uses synthetic data only.
- Not intended for production use.
- Outputs are exploratory and for internal decision support only.
