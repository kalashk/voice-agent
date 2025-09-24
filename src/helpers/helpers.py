import json
import logging
from livekit.agents import (
    JobProcess,
    JobContext,
    AgentSession,
    AgentFalseInterruptionEvent,
    NOT_GIVEN
)
from livekit.plugins import silero, openai, turn_detector
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from helpers.config import TTS_PROVIDER

# Logger for this module
logger = logging.getLogger("agent")

thinking_track = None  # Global track for thinking sounds
aligned_script = False
if TTS_PROVIDER == "cartesia":
    aligned_script = True

# --------------------------
#   Prewarm Function
# --------------------------

def prewarm(proc: JobProcess):
    """
    Preload resources before the agent session starts.
    Here, we load a Voice Activity Detection (VAD) model once,
    and store it in the process userdata for reuse.
    """
    proc.userdata["vad"] = silero.VAD.load()


# --------------------------
#   Customer Profile Loader
# --------------------------

def load_customer_profile(path="src/customer.json") -> dict:
    """
    Load a customer profile from a JSON file.
    Returns a dict with customer information (e.g., name, bank).
    """
    try:
        # Attempt to open and parse the JSON file
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # File missing — log error and return empty dict
        logger.error(f"Customer profile file not found at {path}")
        return {}
    except json.JSONDecodeError as e:
        # JSON syntax error — log error and return empty dict
        logger.error(f"Invalid JSON in customer profile file: {e}")
        return {}

# --------------------------
#   Session Setup
# --------------------------

def setup_session(ctx: JobContext, setup_stt, setup_tts, STT_PROVIDER, TTS_PROVIDER) -> AgentSession:
    """
    Create and configure an AgentSession for handling:
      - LLM (OpenAI GPT model)
      - STT (speech-to-text)
      - TTS (text-to-speech)
      - Turn detection (who's speaking, when to switch)
      - VAD (voice activity detection)
    """

    # Initialize AgentSession with components
    session = AgentSession(
        llm=openai.LLM(model="gpt-4o-mini"),       # Use OpenAI LLM for responses
        stt=setup_stt(STT_PROVIDER),               # Speech-to-Text provider
        tts=setup_tts(TTS_PROVIDER),               # Text-to-Speech provider
        turn_detection=MultilingualModel(),        # Handles multi-language turn-taking
        vad=ctx.proc.userdata["vad"],              # Voice Activity Detection (loaded in prewarm)
        # turn_detection=turn_detector.EOUPlugin()  # Works in Voice_pipeline_agent

        # 🔽 Latency tuning — makes assistant feel more responsive
        min_endpointing_delay=0.25,        # Wait this long before deciding speech has ended
        max_endpointing_delay=2.0,         # Hard stop for silence detection
        min_consecutive_speech_delay=0.05, # Time between two speech segments

        # 🔽 Transcript handling
        use_tts_aligned_transcript=aligned_script,  # Don’t wait for TTS metadata to finalize transcript

        # 🔽 Responsiveness
        preemptive_generation=True,        # Start generating replies while user is still talking

        # 🔽 Defaults (safe values)
        allow_interruptions=True,                 # Allow user to interrupt agent
        min_interruption_words=2,
        min_interruption_duration=0.25,           # Minimum silence to allow interruption
        discard_audio_if_uninterruptible=True,    # Save compute if interruption not possible
        agent_false_interruption_timeout=1.0,     # Grace period after false interruption
    )

    # --------------------------
    #   Event Handlers
    # --------------------------

    @session.on("agent_false_interruption")
    def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
        """
        Handles cases where the agent incorrectly thinks it was interrupted.
        Instead of stopping, resume reply generation.
        """
        logger.info("false positive interruption, resuming")
        session.generate_reply(instructions=ev.extra_instructions or NOT_GIVEN)

    return session
