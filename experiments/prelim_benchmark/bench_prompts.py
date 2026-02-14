"""
Builds prompts for use in the experiment.

Intentionally separate from production prompt_builder.py.
Uses a single standard prompt structure across all model sizes
to isolate raw model capability (Part 1).
"""

import random

from experiments.prelim_benchmark.bench_loader import BenchCase
from src.app.models import ExampleData
import src.app.constants as constants


# Maps target_tier to descriptive label and tone for prompt injection
TIER_CONFIG = {
    "bottom_third": {
        "label": "average performer",
        "tone": "professional and positive but without praise",
    },
    "middle_third": {
        "label": "above-average performer",
        "tone": "professional with light praise, focus on reliability",
    },
    "top_third": {
        "label": "top performer",
        "tone": "highly praiseworthy and strong, highlight impact",
    },
    "water_walker": {
        "label": "exceptional performer (Top 2%)",
        "tone": "distinguished, sets apart, use language like 'unprecedented' or 'vital'",
    },
}

# Maps tier names to the keys used in ExampleData.examples and ExampleData.recs
# water_walker (singular in ALLOWED_TIERS) -> water_walkers (plural in YAML)
_EXAMPLE_KEY_MAP = {
    "bottom_third": "bottom_third",
    "middle_third": "middle_third",
    "top_third": "top_third",
    "water_walker": "water_walkers",
}


def _get_random_recs(recs, example_key):
    """Returns a (promotion_rec, assignment_rec) tuple for the given tier key."""
    pool = recs.get(example_key, {})

    def pick(category):
        opts = pool.get(category, [])
        if not opts:
            return ""
        choice = random.choice(opts)
        # "None." entries mean no recommendation for this tier
        return "" if "none" in choice.lower() else choice

    return pick("promotion"), pick("assignment")


def base_prompt_builder(case: BenchCase, example_data: ExampleData) -> tuple[str, str]:
    """
    Builds standard prompt for benchmarking across all model sizes.

    Args:
        case: A single BenchCase from the data loader.
        example_data: ExampleData instance with loaded YAML examples and recs.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    tier_cfg = TIER_CONFIG[case.target_tier]
    example_key = _EXAMPLE_KEY_MAP[case.target_tier]

    # Select a random tier-matched example narrative
    tier_examples = example_data.examples.get(example_key, [])
    example_text = (
        random.choice(tier_examples)["section_i"] if tier_examples else "No example provided."
    )

    # Select random promotion and assignment recommendations
    prom_rec, assign_rec = _get_random_recs(example_data.recs, example_key)
    mandatory_ending = f"{prom_rec} {assign_rec}".strip()

    # System prompt: role, task, structure, constraints
    system_prompt = (
        "You are a United States Marine Reporting Senior writing Section I comments "
        "for a fitness report.\n\n"
        "TASK: Produce a single-paragraph narrative that paints a clear word picture of "
        "the Marine's professional qualities - performance, technical proficiency, character, "
        "leadership, intellect, and overall impact - inferred from his ACCOMPLISHMENTS. "
        "The narrative must reflect the assigned performance tier and read as an authoritative "
        "command assessment.\n\n"
        "NARRATIVE STRUCTURE:\n"
        "- Opening: One to two sentences that use two-three descriptive adjectives to describe "
        "the total Marine and address overall impact or performance.\n"
        "- Body: A short paragraph that paints the word picture of the Marine's professional "
        "qualities. Each sentence should describe a specific quality or qualities.\n"
        "- Closing: Use the MANDATORY ENDING provided by the user.\n\n"
        "GUIDELINES:\n"
        "- Do NOT summarize, list, or paraphrase ACCOMPLISHMENTS - use ONLY as evidence to "
        "support your narrative.\n"
        "- Use concise, professional language.\n"
        "- Match descriptive language and tone to the assigned PERFORMANCE TIER.\n"
        "- Match style and structure to the EXAMPLE.\n"
        "- Use ADDITIONAL CONTEXT as extra evidence to shape emphasis and tone.\n\n"
        "CONSTRAINTS:\n"
        f"- Length: {constants.SECT_I_CHAR_LIMIT - 100} to {constants.SECT_I_CHAR_LIMIT} characters.\n"
        "- Structure: One paragraph only.\n"
        "- No Markdown formatting, no bullet points."
    )

    # User prompt: case-specific data
    accomplishments_text = "\n".join(case.accomplishments)
    context_text = case.context if case.context else "No additional context"

    user_prompt = (
        f"Write Section I comments for: {case.rank} {case.name}\n"
        f"BILLET: {case.billet_title}\n"
        f"PERFORMANCE TIER: {tier_cfg['label']} - {tier_cfg['tone']}\n\n"
        f"ACCOMPLISHMENTS:\n{accomplishments_text}\n\n"
        f"ADDITIONAL CONTEXT: {context_text}\n\n"
        f"EXAMPLE:\n{example_text}\n\n"
        f"MANDATORY ENDING: {mandatory_ending}"
    )

    return system_prompt, user_prompt


def small_prompt_builder():
    """
    Builds scaled prompt for benchmarking small (3B - 8B parameter) models.
    """
    pass


def open_prompt_builder():
    """
    Builds scaled prompt for benchmarking open source models (30B - 120B parameter) models.
    """
    pass


def frontier_prompt_builder():
    """
    Builds scaled prompt for benchmarking frontier (mini and full size) models.
    """
    pass
