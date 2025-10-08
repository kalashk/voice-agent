import os
import json
import asyncio
import logging
from livekit.agents import (
    JobProcess,
    JobContext,
    AgentSession,
    AgentFalseInterruptionEvent,
    NOT_GIVEN,
)
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins.turn_detector.english import EnglishModel
from helpers.config import TTS_PROVIDER


# Logger for this module
logger = logging.getLogger("agent")

thinking_track = None  # Global track for thinking sounds
aligned_script = False
if TTS_PROVIDER == "cartesia":
    aligned_script = True

def turn_detector_model(TTS_PROVIDER):
    if TTS_PROVIDER == "cartesia": 
        return EnglishModel()
    return MultilingualModel()
# --------------------------
#   Prewarm Function
# --------------------------

def prewarm(proc: JobProcess):
    """
    Preload resources before the agent session starts.
    Here, we load a Voice Activity Detection (VAD) model once,
    and store it in the process userdata for reuse.
    """
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.1,        # require 100ms of speech to start
        min_silence_duration=0.35,      # slightly longer pause before marking end
        prefix_padding_duration=0.2,    # small padding before speech start
        max_buffered_speech=45.0,       # enough buffer for normal latency
        activation_threshold=0.6,       # stricter threshold = less false triggers
        sample_rate=16000,
        force_cpu=True
    )


# --------------------------
#   Session Setup
# --------------------------

def setup_session(ctx: JobContext, setup_llm, setup_stt, setup_tts, LLM_PROVIDER, STT_PROVIDER, TTS_PROVIDER) -> AgentSession:
    """
    Create and configure an AgentSession for handling:
      - LLM (OpenAI GPT model)
      - STT (speech-to-text)
      - TTS (text-to-speech)
      - Turn detection (who's speaking, when to switch)
      - VAD (voice activity detection)
    """

    # Noise Cancellation
    # Initialize AgentSession with components
    session = AgentSession(
        llm=setup_llm(LLM_PROVIDER),       # Use OpenAI LLM for responses
        stt=setup_stt(STT_PROVIDER),               # Speech-to-Text provider
        tts=setup_tts(TTS_PROVIDER),               # Text-to-Speech provider
        turn_detection=turn_detector_model(TTS_PROVIDER),        # Handles multi-language turn-taking
        vad=ctx.proc.userdata["vad"],              # Voice Activity Detection (loaded in prewarm)

        # 🔽 Latency tuning — makes assistant feel more responsive
        min_endpointing_delay=0.25,        # Wait this long before deciding speech has ended
        max_endpointing_delay=2.0,         # Hard stop for silence detection
        min_consecutive_speech_delay=0.15, # Time between two speech segments

        # 🔽 Transcript handling
        use_tts_aligned_transcript=aligned_script,  # Don’t wait for TTS metadata to finalize transcript

        # 🔽 Responsiveness
        preemptive_generation=True,        # Start generating replies while user is still talking

        # 🧏 Interruptions – smoother and less aggressive
        allow_interruptions=True,
        min_interruption_duration=0.15,   # require 150ms of user speech to count as real interruption
        min_interruption_words=1,        # only if STT is enabled
        discard_audio_if_uninterruptible=False,  # keep audio even if agent is mid-sentence
        agent_false_interruption_timeout=2.0,    # quicker recovery if user stopped
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

    # @session.on("user_state_changed")
    # async def handle_user_speaking(event):
    #     # Detect if user started talking
    #     if event.new_state == "speaking":
    #         # If agent was speaking, treat it as interruption
    #         if session.agent_state == "speaking":
    #             print("⚠️ User interrupted agent. Pausing for 2 seconds...")

    #             # Stop current TTS playback (speech handle)
    #             if session._active_speech:
    #                 await session._active_speech.cancel()

    #             # Wait 2 seconds before listening again
    #             await asyncio.sleep(2)
    #             print("🕓 Listening again...")



    return session