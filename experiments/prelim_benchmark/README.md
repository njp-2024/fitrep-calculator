# Model Benchmark Harness

This directory contains the experimental framework for evaluating LLM capability and workflow integration for structured narrative generation tasks.

This harness is **separate from the production app** and is used exclusively for controlled capability screening and internal experimentation.

---

## Current Status

The benchmark harness is in its initial setup phase.

Currently implemented:

- Standalone experiment entry point (`run_benchmark.py`)
- Successful import of production LLM client
- Verified API connectivity
- Successful test generation using default model

Not yet implemented:

- Structured run logging
- Multi-case execution
- Multi-model execution
- Synthetic dataset integration
- Rating export pipeline



---

## Purpose

This harness will support:

1. Standardized capability benchmarking across model classes.
2. Deployment realism benchmarking.
3. Export of blinded outputs for human rating.

---


## Directory Structure

```
model_benchmark/
│
├── run_benchmark.py        # Entry point for benchmark runs
├── data/                   # Synthetic datasets (versioned)
├── config/                 # Benchmark configuration files
├── outputs/
└── README.md
```

---

## Running the Smoke Test

From the project root:

```bash
python -m experiments.model_benchmark.run_benchmark
```

---

## Notes

- The experiment will use synthetic data only.
- Not intended for production use.
- Outputs are exploratory and for internal decision support only.

---

## Future Additions

- Run logging
- Multi-model execution loop
- Synthetic case generator
- Blind rating export
- Aggregate metrics reporting
- Automated summary generation

