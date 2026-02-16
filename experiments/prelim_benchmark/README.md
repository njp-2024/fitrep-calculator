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
- Evaluation sampling and packet preparation for Part B human eval (`eval_split.py`)

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
├── eval_split.py           # Evaluation sampling and packet builder (Part B)
├── bench_constants.py      # Model registries, allowed tiers
├── bench_export.py         # Structured output writers (manifest, results, survey CSV)
├── bench_loader.py         # Synthetic dataset loader
├── bench_logger.py         # BenchResult dataclass and run logger
├── bench_prompts.py        # Prompt builders for benchmark use
├── data/
│   └── synthetic_cases_v1.json
├── config/
└── outputs/
    ├── runs/
    │   └── {run_id}/
    │       ├── manifest.json   # Run metadata, models, generation params
    │       ├── results.json    # Full BenchResult data
    │       └── survey.csv      # Blinded, shuffled rows for human evaluation
    └── eval_{timestamp}/
        ├── manifest.json              # Split parameters, counts, random seed
        ├── summary.txt                # Human-readable overview of the split
        ├── llm_eval/
        │   ├── llm_set_wave1_only.csv # LLM eval set if only wave 1 runs
        │   └── llm_set_both_waves.csv # LLM eval set if both waves run
        ├── human_eval/
        │   ├── wave1/
        │   │   └── wave1_packet_*.txt # 12 blinded survey packets
        │   ├── wave2/
        │   │   └── wave2_packet_*.txt # 12 blinded survey packets
        │   └── sample_assignments.csv # Unblinding key for post-analysis
        └── calibration/
            └── calibration_set.csv    # Samples for human+LLM agreement check
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

## Evaluation Sampling (Part B)

After a Part B (scaled prompts) benchmark run completes, use `eval_split.py` to split outputs into human-eval and LLM-eval sets and generate survey packets.

```bash
python -m experiments.prelim_benchmark.eval_split \
    --run-dir outputs/runs/YYYYMMDD_scaled \
    --seed 42
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--run-dir` | required | Path to a completed Part B run directory (containing `results.json`) |
| `--seed` | `42` | Random seed for reproducible sampling |

### Sampling strategy

- **Matrix**: 8 models x 4 tiers = 32 cells, 5 cases per cell (160 total outputs)
- **Stratified sample**: 1 random sample per cell per wave (32 per wave, 64 total across 2 waves)
- **Packets**: 12 per wave, 8 narratives each, built via circular rotation over a tier-interleaved list
- **Tier balance**: exactly 2 narratives per tier in each packet
- **Overlap**: each sample appears in exactly 3 of the 12 packets within its wave
- **Calibration**: ~10 wave 1 samples are flagged for dual human+LLM evaluation (agreement metrics)
- **LLM remainder**: 160 - 64 = 96 outputs go to LLM-only evaluation

### Wave usage

- **Wave 1**: 12 packets for the initial 12 evaluators
- **Wave 2**: 12 additional packets if 12+ more evaluators volunteer
- **3-4 extra evaluators**: reuse wave 1 packets instead of deploying wave 2

---

## Output Files

### Benchmark run outputs

Each run creates `outputs/runs/{run_id}/` containing:

- **manifest.json** -- Run metadata: prompt mode, notes, model list, temperature, max_tokens
- **results.json** -- Full generation results (text, token counts, latency, errors)
- **survey.csv** -- Blinded and shuffled rows for building human evaluation surveys. Contains case context and generated narrative but no model identity.

### Evaluation split outputs

Each eval split creates `outputs/eval_{timestamp}/` containing:

- **manifest.json** -- Split parameters, seed, and sample counts
- **summary.txt** -- Human-readable overview: tier/model distributions, packet contents, sample appearance counts
- **human_eval/wave1/** and **wave2/** -- Plain `.txt` packet files for survey distribution (blinded, no model identity)
- **human_eval/sample_assignments.csv** -- Master unblinding key linking evaluation IDs to models, waves, and packets
- **llm_eval/llm_set_wave1_only.csv** -- 128 outputs for LLM eval if only wave 1 is used
- **llm_eval/llm_set_both_waves.csv** -- 96 outputs for LLM eval if both waves are used
- **calibration/calibration_set.csv** -- Samples receiving both human and LLM evaluation for agreement analysis

---

## Notes

- The experiment uses synthetic data only.
- Not intended for production use.
- Outputs are exploratory and for internal decision support only.
