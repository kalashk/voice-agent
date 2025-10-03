import uuid
from pathlib import Path
from datetime import timezone, timedelta

#TTS_PROVIDER = "cartesia"
TTS_PROVIDER = "sarvam_anushka"
#TTS_PROVIDER = "sarvam_manisha"  

# STT_PROVIDER = "deepgram"
STT_PROVIDER = "sarvam"

#LLM_PROVIDER = "gemini"
LLM_PROVIDER = "openai"

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Path for storing logs
LOG_PATH = BASE_DIR.parent / "logs"
# Ensure logs directory exists
LOG_PATH.mkdir(exist_ok=True)

# Define IST timezone (+5:30 from UTC)
IST = timezone(timedelta(hours=5, minutes=30))

# Unique session ID for tracking each run
SESSION_ID = str(uuid.uuid4())

# Dictionary to hold structured logs for this session
SESSION_LOGS = {
    "metadata": {}, "transcript": [], "stt": [], 
    "llm": [], "tts": [], "eou": [], "conversation": []
}

THINKING_PROBABILITY = 1 # Probability of playing a thinking sound before replies

COST_PATH = Path("src/costs")