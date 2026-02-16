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
    "Llama 3.2 3B" : {
        "model_id": "llama3.2:3b-instruct-q4_K_M",
        "size_category": MODEL_SIZE_SMALL
    }
}

OPEN_WEIGHT_MODELS = {
    # "Qwen2.5 72B": {
    #     "model_id": "Qwen/Qwen2.5-72B-Instruct",
    #     "size_category": MODEL_SIZE_LARGE,
    # },
    "Qwen3 32B": {
        "model_id": "Qwen/Qwen3-32B",
        "size_category": MODEL_SIZE_MID,
        "reasoning": True,
    },
    # "Qwen3 Next 80B": {
    #     "model_id": "Qwen/Qwen3-Next-80B-A3B-Instruct",
    #     "size_category": MODEL_SIZE_LARGE,
    #     "reasoning": True,
    # },
    # "gpt-oss-120b" : {
    #     "model_id": "openai/gpt-oss-120b",
    #     "size_category": MODEL_SIZE_LARGE,
    #     "reasoning": True,
    # },
    # "Qwen3 235B": {
    #     "model_id": "Qwen/Qwen3-235B-A22B-Instruct-2507",
    #     "size_category": MODEL_SIZE_LARGE,
    #     "reasoning": True,
    # },
    "Llama 3.3 70B": {
        "model_id": "meta-llama/Llama-3.3-70B-Instruct",
        "size_category": MODEL_SIZE_LARGE,
    },
    "Llama 3.1 8B": {
        "model_id": "meta-llama/Llama-3.1-8B-Instruct",
        "size_category": MODEL_SIZE_SMALL,
    },
    # "Llama 4 Maverick 17B-128E": {
    #     "model_id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
    #     "size_category": MODEL_SIZE_LARGE
    # },
    "Llama 4 Scout 17B-16E": {
        "model_id": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "size_category": MODEL_SIZE_LARGE
    }
}

FRONTIER_MODELS = {
    # "GPT-4o-mini": {
    #     "model_id": "gpt-4o-mini",
    #     "size_category": MODEL_SIZE_LARGE,
    # },
    # "GPT-5-mini": {
    #     "model_id": "gpt-5-mini",
    #     "size_category": MODEL_SIZE_LARGE,
    # },
    "GPT-4.1-mini": {
        "model_id": "gpt-4.1-mini",
        "size_category": MODEL_SIZE_LARGE,
    },
    "GPT-4.1-nano": {
        "model_id": "gpt-4.1-nano",
        "size_category": MODEL_SIZE_LARGE,
    },
    # "GPT-5-nano": {
    #     "model_id": "gpt-5-nano",
    #     "size_category": MODEL_SIZE_LARGE,
    # },
}

# Generation parameters
TEMPERATURE = 0.7
MAX_TOKENS = 500
MAX_TOKENS_REASONING = 5000  # reasoning models need more tokens for chain-of-thought
