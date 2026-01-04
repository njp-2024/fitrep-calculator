import random
import src.app.constants as constants
import src.app.prompt_templates as templates


def _get_tier_config(rv):
    """Returns the configuration (key, label, tone) for a given RV."""
    if rv < constants.TIER_BOTTOM:
        return {
            'key': 'bottom_third',
            'label': 'low performer',
            'tone': "professional and positive but without praise."
        }
    elif rv < constants.TIER_MIDDLE:
        return {
            'key': 'middle_third',
            'label': 'average performer',
            'tone': "professional with light praise. Focus on reliability."
        }
    elif rv < constants.TIER_TOP:
        return {
            'key': 'top_third',
            'label': 'top performer',
            'tone': "highly praiseworthy and strong. Highlight impact."
        }
    else:
        return {
            'key': 'water_walkers',
            'label': 'exceptional performer (Top 2%)',
            'tone': "distinguished, sets him apart. Use language like 'unprecedented' or 'vital'."
        }


def _get_random_recs(recs, key):
    """Helper to safely fetch a random promotion and assignment recommendation."""
    pool = recs.get(key, {})

    def pick(cat):
        opts = pool.get(cat, [""])
        choice = random.choice(opts)
        # If the config says "none" (e.g. for low performers), return empty string
        return "" if "none" in choice.lower() else choice

    return pick('promotion'), pick('assignment')


# --- Public Methods ---

def build_foundation_prompt(example_data, rpt):
    """
    Constructs a complex System/User prompt pair for Foundation Models (GPT-4o).
    """
    examples = example_data.examples
    recs = example_data.recs

    config = _get_tier_config(rpt.rv_cum)

    # Select dynamic content
    tier_examples = examples.get(config['key'], [])
    example_text = random.choice(tier_examples)['section_i'] if tier_examples else "No example provided."
    prom_rec, assign_rec = _get_random_recs(recs, config['key'])

    s_prompt = (
        f"You are a Marine Corps fitness report writing assistant.\n"
        f"Your goal is to write a Section I narrative that evaluates performance, character, leadership, intellect, and impact.\n\n"
        f"CRITICAL RULES:\n"
        f"1. NO BULLET POINTS. Write a flowing narrative.\n"
        f"2. ATTRIBUTES OVER ACTIONS: Do not merely restate accomplishments. Use them to infer traits.\n"
        f"3. TONE: {config['tone']}\n"
        f"4. LENGTH: 1200-1250 characters.\n"
    )

    user_context = rpt.context if rpt.context else "No additional context"
    u_prompt = (
        f"Write Section I comments for {rpt.rank} {rpt.name}.\n"
        f"Performance Level: {config['label']} (RV: {rpt.rv_cum:.2f})\n\n"
        f"Style Reference (Mimic this structure):\n{example_text}\n\n"
        f"Context: {user_context}\n"
        f"Accomplishments: {rpt.accomplishments}\n\n"
        f"Mandatory Ending: {prom_rec} {assign_rec}"
    )

    return s_prompt, u_prompt


def build_open_weights_prompt(example_data, rpt):
    """
    Constructs a System/User prompt pair for high-end Open Weight models
    (Qwen 72B, Mixtral 8x7B, Llama 3 70B).

    These models are capable of adhering to negative constraints and roles,
    so we use a structure similar to the foundation prompt.
    """
    examples = example_data.examples
    recs = example_data.recs

    config = _get_tier_config(rpt.rv_cum)

    # 1. Select dynamic content
    tier_examples = examples.get(config['key'], [])
    example_text = random.choice(tier_examples)['section_i'] if tier_examples else "No example provided."
    prom_rec, assign_rec = _get_random_recs(recs, config['key'])

    # 2. System Prompt: Role & Rules
    # slightly adjusted for Qwen/Mixtral which prefer very explicit formatting rules
    s_prompt = (
        f"You are an expert US Marine Corps Fitness Report writer.\n"
        f"Your task is to write a Section I narrative evaluating character, leadership, and impact.\n\n"
        f"STRICT OUTPUT RULES:\n"
        f"1. OUTPUT FORMAT: A single paragraph of text. NO Markdown formatting, NO bullet points.\n"
        f"2. LENGTH: Between 1200 and 1250 characters.\n"
        f"3. TONE: {config['tone']}\n"
        f"4. CONTENT: Infer traits from the provided accomplishments. Do not just list them.\n"
    )

    # 3. User Prompt: Data & Context
    user_context = rpt.context if rpt.context else "No additional context"

    u_prompt = (
        f"Write Section I comments for {rpt.rank} {rpt.name}.\n"
        f"Performance Tier: {config['label']} (RV: {rpt.rv_cum:.2f})\n\n"

        f"REFERENCE STYLE (Mimic this sentence structure):\n"
        f"\"{example_text}\"\n\n"

        f"CONTEXT NOTES:\n{user_context}\n\n"

        f"ACCOMPLISHMENTS:\n{rpt.accomplishments}\n\n"

        f"MANDATORY ENDING: {prom_rec} {assign_rec}"
    )

    return s_prompt, u_prompt


def build_local_prompt(example_data, rpt):
    """
    Constructs a single simplified prompt string for Local Models (Mistral/Llama).
    """
    examples = example_data.examples

    config = _get_tier_config(rpt.rv_cum)

    tier_examples = examples.get(config['key'], [])
    example_text = random.choice(tier_examples)['section_i'] if tier_examples else ""

    user_context = rpt.context if rpt.context else "No additional context"
    return (
        f"Write a US Marine Corps Fitness Report narrative for {rpt.rank} {rpt.name}.\n"
        f"Level: {config['label']}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. {config['tone']}\n"
        f"2. Infer traits from the accomplishments below.\n"
        f"3. Write exactly one paragraph (~1200 chars).\n\n"
        f"STYLE EXAMPLE:\n{example_text}\n\n"
        f"INPUT DATA:\n"
        f"Context: {user_context}\n"
        f"Accomplishments: {rpt.accomplishments}\n"
        f"RESPONSE:"
    )



####################################################################################
#################################  For testing #####################################
####################################################################################

if __name__ == "__main__":
    pass
