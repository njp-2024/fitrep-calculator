import shutil

# App version - single source of truth
APP_VERSION = "0.2.0"

# fitrep constants
SCORE_LETTER_VALS = ["A", "B", "C", "D", "E", "F", "G", "H"]

SCORE_MAP = {
    "A" : 1,
    "B" : 2,
    "C" : 3,
    "D" : 4,
    "E" : 5,
    "F" : 6,
    "G" : 7,
    "H" : 0  # H is actually not counted at all, so this value should never factor into calculations
}

USMC_RANKS = [
    "Sgt", "SSgt", "GySgt", "MSgt", "1stSgt", "MGySgt", "SgtMaj",
    "2ndLt", "1stLt", "Capt", "Maj", "LtCol", "Col"
]

USMC_CATEGORIES = [
    "Performance", "Proficiency", "Courage",
    "Effectiveness Under Stress", "Initiative", "Leading Subordinates",
    "Developing Subordinates", "Setting the Example", "Ensuring Well-being",
    "Communication Skills", "PME", "Decision Making",
    "Judgment", "Reports"
]

TIER_BOTTOM = 86.67
TIER_MIDDLE = 93.34
TIER_TOP = 98.0
# eliter/water walker is above 98.0


# Model dicts
# Format: {'Display Name' : 'model_id'}

# default: mistral:7b-instruct-v0.3-q4_K_M, others:
DEFAULT_LOCAL_MODEL = "mistral:7b-instruct-v0.3-q4_K_M"
LOCAL_MODELS = {"Mistral 7B" : "mistral:7b-instruct-v0.3-q4_K_M"}

# default: Qwen/Qwen2.5-72B-Instruct, others:
DEFAULT_OPEN_MODEL = "Qwen/Qwen2.5-72B-Instruct"
OPEN_WEIGHT_MODELS = {"Qwen 72B" : "Qwen/Qwen2.5-72B-Instruct"}

# default: gpt-4o-mini, others: gpt-5.1, gpt-5-mini, gpt-5-nano
DEFAULT_FRONTIER_MODEL = "gpt-4o-mini"
FRONTIER_MODELS = {"GPT-4o-mini" : "gpt-4o-mini",
                   "GPT-5-mini" : "gpt-5-mini",
                   "GPT-5-nano" : "gpt-5-nano",
                   "GPT-4.1-mini" : "gpt-4.1-mini",
                   "GPT-4.1-nano" : "gpt-4.1-nano"}

# LLM Constants
FOUNDATION_TEMP = 1.0    # base of .2, increased to increase creativity
LOCAL_TEMP = 0.7
OPEN_TEMP = 0.7

FOUNDATION_MAX_TOKENS = 500
LOCAL_MAX_TOKENS = 500
OPEN_MAX_TOKENS = 500

MIN_ACCOMPLISHMENTS_LENGTH = 50
MAX_ACCOMPLISHMENTS_LENGTH = 1500
MAX_USER_CONTEXT_LENGTH = 800

# If you are using the local option on your machine, make sure these constants are set based on your set up
# See README.md for instructions

# attempt to find ollama automatically
OLLAMA_PATH = shutil.which("ollama")

# if that doesn't work, set path explicitly
# OLLAMA_PATH = r"C:\Users\nicho\AppData\Local\Programs\Ollama\ollama.exe"


# other
CATEGORIES_YAML = ["performance", "proficiency", "individual_character", "effectiveness_under_stress", "initiative",
                   "leading_subordinates", "developing_subordinates"]
