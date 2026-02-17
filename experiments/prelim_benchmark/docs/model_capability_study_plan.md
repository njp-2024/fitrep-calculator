# Model Capability Study Plan

## Overview

This study is a rapid, exploratory capability screening designed to inform AI
deployment strategy for structured performance narrative generation tasks. It
evaluates how well different LLMs -- ranging from small local models to frontier
APIs -- can generate fitrep Section I narrative drafts given synthetic input
data and scaled prompts.

The original design had two parts:
- **Part A** -- Uniform prompt across all models (isolates raw capability)
- **Part B** -- Scaled prompts matched to model size (tests whether simple
  prompt engineering closes capability gaps)

**Part A was canceled.** The study proceeds with Part B only, using scaled
prompts. The rationale: raw capability without any prompt tuning is less
relevant to deployment decisions than capability with lightweight, practical
prompt scaling.

This is not a publication-grade study. It is meant to produce directional
findings for internal decision-making.

---

## Study Design

### Models Under Test

9 models across 3 deployment tiers:

| Model | Size Category | Client | Reasoning |
|-------|--------------|--------|-----------|
| Llama 3.2 3B | Small (3-8B) | Local (Ollama) | No |
| Mistral 7B | Small (3-8B) | Local (Ollama) | No |
| Llama 3.1 8B | Small (3-8B) | HuggingFace | No |
| Qwen3 32B | Mid (20-30B) | HuggingFace | Yes |
| Llama 3.3 70B | Large (70B+) | HuggingFace | No |
| Llama 4 Scout 17B-16E | Large | HuggingFace | No |
| GPT-4.1-nano | Large | OpenAI | No |
| GPT-4.1-mini | Large | OpenAI | No |
| GPT-5.2 | Large | OpenAI | Yes |

### Prompt Scaling Strategy (Part B)

System prompts are scaled by model size category. User prompts remain identical
across all models to preserve the experimental contract.

| Size Category | Prompt Builder | Description |
|--------------|----------------|-------------|
| Small (3-8B) | `small_prompt_builder` | Condensed system prompt; reduced cognitive load, simplified structure |
| Mid (20-30B) | `mid_prompt_builder` | Full task description; merged guidelines and constraints into single Rules section |
| Large (70B+) | `base_prompt_builder` | Full system prompt with separate TASK, NARRATIVE STRUCTURE, GUIDELINES, and CONSTRAINTS sections |

All prompts include:
- Role assignment (Marine Reporting Senior)
- Task description (single-paragraph narrative)
- Narrative structure (opening, body, closing)
- Tier-matched tone and language guidance
- A randomly selected tier-matched example narrative
- A randomly selected mandatory ending (promotion/assignment recommendations)
- Character limit constraints

### Synthetic Data

- **Dataset**: `synthetic_cases_v1.json` (20 cases)
- **Tiers**: 4 tiers (bottom_third, middle_third, top_third, water_walker), 5
  cases per tier
- **Per case**: rank, name, billet_title, accomplishments (5-7 bullets),
  context, target_tier
- All data is synthetic. No real personnel or events are represented.

### Generation Parameters

| Parameter | Value      |
|-----------|------------|
| Temperature | 0.7        |
| Max tokens (standard) | 500        |
| Max tokens (reasoning models) | 5,000      |
| Target character range | 956 - 1056 |

### Experimental Matrix

- **9 models x 20 cases = 180 total generations**
- Each model generates a narrative for every case
- Each generation is logged with: text, character count, prompt tokens,
  completion tokens, latency, error status, and prompt builder used

---

## Procedure

### Benchmark Execution

1. Load the synthetic dataset (20 cases, 4 tiers)
2. Load example narratives and recommendation text from YAML files
3. Initialize LLM clients for all 9 models
4. For each model:
   a. Select the prompt builder matching the model's size category
   b. For each case:
      - Build system and user prompts (with random example and mandatory ending)
      - Send request to the model
      - Log the result (text, tokens, latency, errors)
5. Save structured output (manifest, results, survey CSV)

Run command:
```bash
python -m experiments.prelim_benchmark.run_benchmark --prompt-mode scaled
```

### Evaluation Sampling

After the benchmark run completes, `eval_split.py` splits the 180 outputs into
human-eval and LLM-eval sets.

```bash
python -m experiments.prelim_benchmark.eval_split \
    --run-dir outputs/runs/{run_id} \
    --seed 42
```

**Sampling strategy:**
- Stratified sample: 1 random output per model-tier cell per wave
- 32 samples per wave, 64 total across 2 waves
- 12 packets per wave, 8 narratives each
- Tier balance: exactly 2 narratives per tier in each packet
- Overlap: each sample appears in exactly 3 of the 12 packets within its wave
- Calibration: ~10 wave 1 samples flagged for dual human + LLM evaluation
- LLM remainder: 180 - 64 = 116 outputs go to LLM-only evaluation

**Wave usage:**
- Wave 1: 12 packets for the initial 12 evaluators
- Wave 2: 12 additional packets if 12+ more evaluators volunteer
- 3-4 extra evaluators: reuse wave 1 packets instead of deploying wave 2

### Human Evaluation

Evaluators receive blinded survey packets (no model identity visible). Each
packet contains 8 narratives with case context (rank, name, billet,
accomplishments, target tier) and the generated narrative.

Per narrative, evaluators answer 5 questions:
1. **Tier Alignment** (1-5 scale) -- Does the narrative match the indicated
   performance tier?
2. **Overall Quality** (1-5 scale) -- How would you rate the overall quality?
3. **Accomplishment Coverage** (1-5 scale) -- Does the narrative incorporate
   the listed accomplishments?
4. **Usability** (single choice) -- Would you use this as a starting draft?
5. **Comments** (optional free text) -- Any specific issues or observations?

See `survey_questions.md` for the complete question text formatted for Google
Forms.

---

## Data Captured

| Data Point | Source |
|------------|--------|
| Generated narrative text | Benchmark run |
| Character count | Benchmark run |
| Prompt token count | Benchmark run |
| Completion token count | Benchmark run |
| Latency (seconds) | Benchmark run |
| Errors | Benchmark run |
| Prompt builder used | Benchmark run |
| Tier alignment rating | Human evaluation |
| Overall quality rating | Human evaluation |
| Accomplishment coverage rating | Human evaluation |
| Usability assessment | Human evaluation |
| Evaluator comments | Human evaluation |

---

## Analysis Approach

Given the exploratory nature and sample sizes:

- **Quantitative**: Descriptive statistics (median, distribution) for scale
  questions, grouped by model and by tier. No inferential statistics planned.
- **Model comparison**: Median ratings across quality dimensions, grouped by
  model size category and individual model.
- **Tier analysis**: Whether models handle certain tiers (e.g., water_walker
  vs. bottom_third) better or worse.
- **Usability rate**: Percentage of narratives evaluators would use as a
  starting draft, by model.
- **Qualitative**: Thematic grouping of evaluator comments to identify common
  strengths and failure modes.
- **Calibration**: Compare human and LLM ratings on the calibration set to
  assess agreement.

### Key Questions

1. Which models produce narratives that evaluators would actually use as drafts?
2. Do larger models consistently outperform smaller ones, or are there
   diminishing returns?
3. Does prompt scaling close the gap between small and large models?
4. Are certain performance tiers harder for models to match?
5. What are the most common failure modes (tone, content, structure)?

---

## Output Structure

```
outputs/
├── runs/{run_id}/
│   ├── manifest.json       # Run metadata, models, generation params
│   ├── results.json        # Full generation results
│   └── survey.csv          # Blinded, shuffled rows for evaluation
└── eval_{timestamp}/
    ├── manifest.json
    ├── summary.txt
    ├── human_eval/
    │   ├── wave1/wave1_packet_*.txt
    │   ├── wave2/wave2_packet_*.txt
    │   └── sample_assignments.csv
    ├── llm_eval/
    │   ├── llm_set_wave1_only.csv
    │   └── llm_set_both_waves.csv
    └── calibration/
        └── calibration_set.csv
```

---

## Limitations

- Synthetic data only; may not capture the full complexity of real fitrep cases
- Small evaluator sample with overlapping packet assignments
- No repeated measures (each output evaluated by ~3 evaluators, not all)
- Prompt scaling is lightweight (system prompt only); does not explore
  few-shot, chain-of-thought, or other advanced techniques
- Temperature fixed at 0.7; no exploration of generation parameter sensitivity
- Random example and mandatory ending selection introduces minor run-to-run
  variance

---

## Notes

- Benchmark harness is intentionally separate from production code
  (`bench_prompts.py` does not reuse `prompt_builder.py`)
- All data is synthetic. No real personnel or accomplishments are used.
- Results are for internal decision support only.
