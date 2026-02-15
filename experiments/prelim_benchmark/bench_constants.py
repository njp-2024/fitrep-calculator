ALLOWED_TIERS = {"bottom_third", "middle_third", "top_third", "water_walker"}

# Size category constants
MODEL_SIZE_SMALL = "small"   # 3B-8B  -> small_prompt_builder
MODEL_SIZE_MID   = "mid"     # 20B-30B -> mid_prompt_builder
MODEL_SIZE_LARGE = "large"   # 70B+   -> base_prompt_builder

LOCAL_MODELS = {
    "Mistral 7B": {
        "model_id": "mistral:7b-instruct-v0.3-q4_K_M",
        "size_category": MODEL_SIZE_SMALL,
    },
}

OPEN_WEIGHT_MODELS = {
    "Qwen 72B": {
        "model_id": "Qwen/Qwen2.5-72B-Instruct",
        "size_category": MODEL_SIZE_MID,
    },
}

FRONTIER_MODELS = {
    "GPT-4o-mini": {
        "model_id": "gpt-4o-mini",
        "size_category": MODEL_SIZE_LARGE,
    },
}

# Generation parameters
TEMPERATURE = 0.7
MAX_TOKENS = 500
