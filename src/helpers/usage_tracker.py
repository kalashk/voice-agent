import json
import logging
from datetime import datetime

from livekit.agents import metrics

from helpers.config import COST_PATH, IST

# Logger dedicated to usage & cost tracking
logger = logging.getLogger("usage")

# Path to JSON files that store per-service cost configurations
CONFIG_PATH = COST_PATH


# --------------------------
#   Config Loader
# --------------------------

def load_cost_config(service: str) -> dict:
    """
    Load cost configuration JSON for a given service (llm, stt, tts).
    Example: src/costs/llm.json, src/costs/stt.json, src/costs/tts.json
    """
    path = CONFIG_PATH / f"{service}.json"
    if not path.exists():
        raise FileNotFoundError(f"Cost config not found: {path}")
    with open(path) as f:
        return json.load(f)


# --------------------------
#   Cost Calculator
# --------------------------

class CostCalculator:
    """
    Handles cost calculation for:
      - LLM usage (tokens in/out, cached tokens)
      - STT usage (seconds of audio transcribed)
      - TTS usage (characters, tokens, or seconds of audio generated)

    Also records detailed per-event logs with timestamps.
    """

    def __init__(self, stt_provider: str, tts_provider: str, llm_provider: str):
        # Load static pricing configs from JSON files
        self.llm_config = load_cost_config("llm")
        self.stt_config = load_cost_config("stt")
        self.tts_config = load_cost_config("tts")

        # Active providers being used (e.g., OpenAI, Deepgram, ElevenLabs)
        self.stt_provider = stt_provider
        self.tts_provider = tts_provider
        self.llm_provider = llm_provider

        # Store detailed logs for each usage event
        self.events = {
            "stt": [],   # speech-to-text logs
            "tts": [],   # text-to-speech logs
            "llm": []    # language model logs
        }

    # --------------------------
    #   LLM Cost Calculation
    # --------------------------

    def calculate_llm_cost(self, prompt_tokens: int, cached_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost for LLM usage:
          - prompt_tokens = tokens in the prompt
          - cached_tokens = tokens reused from cache (cheaper)
          - completion_tokens = tokens generated in response
        """
        # input_rate = self.llm_config.get(self.llm_provider, {}).get("rate", 0.0)

        # # Load rates (fallbacks in case not defined)
        # input_rate = self.llm_config.get("input_rate", 0.0)
        # cached_rate = self.llm_config.get("cached_input_rate", input_rate)
        # output_rate = self.llm_config.get("output_rate", 0.0)

        cfg = self.llm_config.get(self.llm_provider, {})

        input_rate = cfg.get("input_rate", 0.0)
        cached_rate = cfg.get("cached_input_rate", input_rate)
        output_rate = cfg.get("output_rate", 0.0)



        # Apply cost formula
        cost = (
            (prompt_tokens - cached_tokens) * input_rate +   # normal input
            cached_tokens * cached_rate +                   # cached input
            completion_tokens * output_rate                 # output tokens
        )

        # Record the event with timestamp
        self.events["llm"].append({
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cached_tokens": cached_tokens,
            "timestamp": datetime.now(IST).isoformat() + "Z"
        })

        return round(cost, 6)

    # --------------------------
    #   STT Cost Calculation
    # --------------------------

    def calculate_stt_cost(self, seconds: float) -> float:
        """
        Calculate cost for STT usage:
          - seconds = duration of audio processed
        """

        # Rate depends on the provider
        rate = self.stt_config.get(self.stt_provider, {}).get("rate", 0.0)
        cost = seconds * rate

        # Record the event with timestamp
        self.events["stt"].append({
            "provider": self.stt_provider,
            "seconds": seconds,
            "rate": rate,
            "cost": round(cost, 6),
            "timestamp": datetime.now(IST).isoformat() + "Z"
        })

        return round(cost, 6)

    # --------------------------
    #   TTS Cost Calculation
    # --------------------------

    def calculate_tts_cost(self, characters: int = 0, seconds: float = 0.0, input_tokens: int = 0) -> float:
        """
        Calculate cost for TTS usage:
          - characters = text length synthesized
          - seconds = duration of generated audio
          - input_tokens = tokens sent for synthesis (if provider charges this way)
        """

        cfg = self.tts_config.get(self.tts_provider, {})
        cost = 0.0

        # Apply different pricing models depending on provider
        if "rate_per_character" in cfg:
            cost += characters * cfg["rate_per_character"]
        if "rate_per_second" in cfg:
            cost += seconds * cfg["rate_per_second"]
        if "rate_per_input_token" in cfg:
            cost += input_tokens * cfg["rate_per_input_token"]
        if "rate_per_output_second" in cfg:
            cost += seconds * cfg["rate_per_output_second"]

        # Record the event with UTC timestamp
        self.events["tts"].append({
            "provider": self.tts_provider,
            "characters": characters,
            "seconds": seconds,
            "input_tokens": input_tokens,
            "cost": cost,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

        return round(cost, 6)

    # --------------------------
    #   Usage Summarizer
    # --------------------------

    def summarize_usage(self, usage: metrics.UsageSummary, session_id: str) -> dict:
        """
        Summarize session usage:
          - Collect LLM, STT, TTS usage metrics
          - Compute individual and total costs
          - Return structured cost breakdown
        """

        # Extract usage values (safe defaults if missing)
        prompt_tokens = getattr(usage, "llm_prompt_tokens", 0)
        cached_tokens = getattr(usage, "llm_prompt_cached_tokens", 0)
        completion_tokens = getattr(usage, "llm_completion_tokens", 0)

        stt_seconds = getattr(usage, "stt_audio_duration", 0.0)
        tts_seconds = getattr(usage, "tts_audio_duration", 0.0)
        tts_characters = getattr(usage, "tts_characters_count", 0)

        # Compute individual costs
        llm_cost = self.calculate_llm_cost(prompt_tokens, cached_tokens, completion_tokens)
        stt_cost = self.calculate_stt_cost(stt_seconds)
        tts_cost = self.calculate_tts_cost(seconds=tts_seconds, characters=tts_characters)

        # Compute total session cost
        total_cost = round(llm_cost + stt_cost + tts_cost, 6)

        # Final metadata block (session summary)
        metadata = {
            "session_id": session_id,
            "final_usage": {
                "session_id": session_id,
                "llm_prompt_tokens": prompt_tokens,
                "llm_completion_tokens": completion_tokens,
                "stt_audio_duration": stt_seconds,
                "tts_audio_duration": tts_seconds,
            },
            "final_cost": {
                "llm_cost": llm_cost,
                "stt_cost": stt_cost,
                "tts_cost": tts_cost,
                "total_cost": total_cost,
            }
        }

        # Merge event logs with metadata
        result = {**self.events, "metadata": metadata}

        # Log summary for debugging/monitoring
        logger.info(f"Cost Summary: {result}")

        # Return clean breakdown (to save in DB, display, etc.)
        return {
            "llm_cost": llm_cost,
            "stt_cost": stt_cost,
            "tts_cost": tts_cost,
            "total_cost": total_cost,
        }
