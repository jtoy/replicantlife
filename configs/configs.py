import os
from dotenv import load_dotenv

load_dotenv()

# DECLARE PARAMS HERE
DEBUG = os.getenv("DEBUG", default="1")
LLAMA_URL = os.getenv("LLAMA_URL", default="http://localhost:11434/api")
POWERINF_URL = os.getenv("POWERINF_URL", default="http://localhost:8080")
LLAMA_TIMEOUT = int(os.getenv("LLAMA_TIMEOUT", default="600"))
REDIS_URL = os.getenv("REDIS_URL", default="redis://localhost:6379")
OPENAI_KEY = os.getenv("OPENAI_KEY")
MODEL = os.getenv("MODEL", default="mistral")
MATRIX_SIZE = int(os.getenv("MATRIX_SIZE", default="15"))
SIMULATION_STEPS = int(os.getenv("SIMULATION_STEPS", default="0"))
RUN_REPORTS = int(os.getenv("RUN_REPORTS", default="1"))
PERCEPTION_RANGE = int(os.getenv("PERCEPTION_RANGE", default="5"))
NUM_AGENTS = int(os.getenv("NUM_AGENTS", default="0"))
NUM_ZOMBIES = int(os.getenv("NUM_ZOMBIES", default="0"))
WARP = int(os.getenv("WARP", default="0"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", default="1"))
IGNORE_PROB = float(os.getenv("IGNORE_PROB", default="0.75"))
ALLOW_MOVEMENT = int(os.getenv("ALLOW_MOVEMENT", default="1"))
SLEEP_STEP = float(os.getenv("SLEEP_STEP", default=0))
CLEAR_TEST_MEMORIES = int(os.getenv("CLEAR_TEST_MEMORIES", default=0))
REFLECT_THRESHOLD = int(os.getenv("REFLECT_THRESHOLD", default=0))
LLM_ACTION = int(os.getenv("LLM_ACTION", default=0))
PRINT_MAP = int(os.getenv("PRINT_MAP", default=0))
TEST_RUN = int(os.getenv("TEST_RUN", default=0))
ALLOW_PLAN = int(os.getenv("ALLOW_PLAN", default=0))
ALLOW_REFLECT = int(os.getenv("ALLOW_REFLECT", default=1))
ALLOW_META = int(os.getenv("ALLOW_META", default=1))
SHORT_MEMORY_CAPACITY = int(os.getenv("SHORT_MEMORY_CAPACITY", default=100))
LOG_TO_REDIS = int(os.getenv("LOG_TO_REDIS", default="1"))
MEMORY_QUERY_COUNT = int(os.getenv("MEMORY_QUERY_COUNT", default="20"))
CONVERSATION_DEPTH = int(os.getenv("CONVERSATION_DEPTH", default="5"))
CONVERSATION_COOLDOWN = int(os.getenv("CONVERSATION_COOLDOWN", default="5"))
LLM_IMPORTANCE = int(os.getenv("LLM_IMPORTANCE", default="0"))
ALLOW_OBSERVANCE = int(os.getenv("ALLOW_OBSERVANCE", default="1"))


# DEV DEFAULTS
DEFAULT_NAMES = ['Alice', 'Bob', 'Charlie', 'David', 'Eva', 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack', 'Katie', 'Leo', 'Mia', 'Nathan', 'Olivia', 'Peter', 'Quinn', 'Rachel', 'Sam', 'Tom', 'Ursula', 'Victor', 'Wendy', 'Xander', 'Yvonne', 'Zach']
DEFAULT_DESCRIPTIONS = [
    "Energetic and outgoing, the life of any friendship circle.",
    "Reserved and contemplative, occasionally distant or aloof.",
    "Charming and witty, spreading joy through laughter.",
    "Awkwardly sweet, navigating the social scene with endearing moments.",
    "Gentle and shy, finding joy in the small, quiet moments.",
    "Confident and sociable, engaging in lively conversations with everyone.",
    "Kind-hearted and considerate, ensuring everyone feels the warmth of friendship.",
    "Quirky and fun-loving, bringing a touch of humor.",
    "Thoughtful and reflective, prone to overthinking small moments.",
    "Friendly and approachable, making everyone feel welcome."
]
DEFAULT_GOALS = [
  "Learn and spread hot gossips.",
  "Build meaningful connections with others.",
  "Learn and share intriguing stories.",
  "Help others in times of need."
]
#DEFAULT_ACTIONS = ["move", "talk", "stay", "continue"]
DEFAULT_ACTIONS = ["move", "talk","continue_to_destination","meta_cognize"]
DEFAULT_QUESTIONS = [
    { "who": "all", "question": "What have you learned so far?" },
    { "who": "all", "question": "What is your most cherished memory and why?" },
    { "who": "all", "question": "What are the locations that you know based on your memories?" }
]
DEFAULT_TIME = 1704067200
