import logging
import uuid
from datetime import datetime

from livekit.agents import (
    AgentSession,
    ConversationItemAddedEvent,
    MetricsCollectedEvent,
    UserInputTranscribedEvent,
    metrics,
)
from livekit.agents.llm import ChatMessage

# from helpers.config import LLM_PROVIDER, TTS_PROVIDER, STT_PROVIDER, IST
from helpers.config import IST, LLM_PROVIDER, STT_PROVIDER, TTS_PROVIDER
from helpers.usage_tracker import CostCalculator

logger = logging.getLogger("agent")


def setup_metrics(session: AgentSession, SESSION_LOGS: dict):  # noqa: N803
    """
    Sets up real-time metrics collection for a LiveKit AgentSession.
    Tracks LLM, STT, TTS, EOU, VAD, and conversation latencies.
    Stores detailed event logs in SESSION_LOGS and returns:
      - usage_collector: aggregates usage metrics
      - cost_calc: cost calculator for billing
    """

    # Aggregate usage metrics across the session
    usage_collector = metrics.UsageCollector()

    # Billing calculator
    cost_calc = CostCalculator(llm_provider=LLM_PROVIDER ,stt_provider=STT_PROVIDER, tts_provider=TTS_PROVIDER)

    # Per-turn temporary store {speech_id: {...metrics...}}
    turn_metrics: dict[str, dict] = {}

    # ------------------------
    # User transcription events
    # ------------------------
    @session.on("user_input_transcribed")
    def _on_user_transcribed(ev: UserInputTranscribedEvent):
        timestamp = datetime.now(IST).isoformat()
        SESSION_LOGS.setdefault("transcript", []).append({
            "speech_id": ev.speaker_id or str(uuid.uuid4()),
            "role": "user",
            "text": ev.transcript.strip(),
            "is_final": ev.is_final,
            "timestamp": timestamp,
        })

    # ------------------------
    # Conversation items (assistant/user messages)
    # ------------------------
    @session.on("conversation_item_added")
    def _on_conversation_item(ev: ConversationItemAddedEvent):
        if isinstance(ev.item, ChatMessage):
            timestamp = datetime.now(IST).isoformat()
            text = ev.item.text_content
            if text:
                SESSION_LOGS.setdefault("transcript", []).append({
                    "speech_id": ev.item.id,
                    "role": ev.item.role,
                    "text": text.strip(),
                    "interrupted": ev.item.interrupted,
                    "confidence": ev.item.transcript_confidence,
                    "timestamp": timestamp,
                })

    # ------------------------
    # Metrics collection
    # ------------------------
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)  # raw log for debugging
        usage_collector.collect(ev.metrics)

        timestamp = datetime.now(IST).isoformat()
        speech_id = getattr(ev.metrics, "speech_id", str(uuid.uuid4()))
        turn_metrics.setdefault(speech_id, {})

        # ---------------- STT ----------------
        if isinstance(ev.metrics, metrics.STTMetrics):
            SESSION_LOGS.setdefault("stt", []).append({
                "speech_id": speech_id,
                "audio_duration": ev.metrics.audio_duration,
                "duration": getattr(ev.metrics, "duration", 0.0),
                "streamed": getattr(ev.metrics, "streamed", False),
                "timestamp": ev.metrics.timestamp,
            })
            turn_metrics[speech_id]["stt_seconds"] = ev.metrics.audio_duration

        # ---------------- LLM ----------------
        elif isinstance(ev.metrics, metrics.LLMMetrics):
            SESSION_LOGS.setdefault("llm", []).append({
                "speech_id": speech_id,
                "duration": ev.metrics.duration,
                "completion_tokens": ev.metrics.completion_tokens,
                "prompt_tokens": ev.metrics.prompt_tokens,
                "prompt_cached_tokens": ev.metrics.prompt_cached_tokens,
                "total_tokens": ev.metrics.total_tokens,
                "tokens_per_second": ev.metrics.tokens_per_second,
                "ttft": ev.metrics.ttft,
                "timestamp": ev.metrics.timestamp,
            })
            turn_metrics[speech_id]["llm_ttft"] = ev.metrics.ttft

        # ---------------- TTS ----------------
        elif isinstance(ev.metrics, metrics.TTSMetrics):
            SESSION_LOGS.setdefault("tts", []).append({
                "speech_id": speech_id,
                "audio_duration": ev.metrics.audio_duration,
                "characters_count": ev.metrics.characters_count,
                "duration": ev.metrics.duration,
                "ttfb": ev.metrics.ttfb,
                "streamed": getattr(ev.metrics, "streamed", False),
                "timestamp": ev.metrics.timestamp,
            })
            turn_metrics[speech_id]["tts_ttfb"] = ev.metrics.ttfb
            turn_metrics[speech_id]["tts_timestamp"] = ev.metrics.timestamp

            # --- Calculate clean latency here ---
            eou = turn_metrics[speech_id].get("eou_delay", 0.0)
            ttft = turn_metrics[speech_id].get("llm_ttft", 0.0)
            ttfb = ev.metrics.ttfb
            total_latency = eou + ttft + ttfb

            SESSION_LOGS.setdefault("conversation", []).append({
                "speech_id": speech_id,
                "latency_seconds": total_latency,
                "stt_seconds": turn_metrics[speech_id].get("stt_seconds", 0.0),
                "llm_ttft": turn_metrics[speech_id].get("llm_ttft", 0.0),
                "tts_ttfb": ev.metrics.ttfb,
                "tts_timestamp": ev.metrics.timestamp,
                "raw_eou_delay": turn_metrics[speech_id].get("eou_delay", 0.0),
                "raw_transcription_delay": turn_metrics[speech_id].get("transcription_delay", 0.0),
                "on_user_turn_completed_delay": turn_metrics[speech_id].get("on_user_turn_completed_delay", 0.0),
                "timestamp": timestamp,
            })
            # cleanup finished turn
            del turn_metrics[speech_id]

        # ---------------- EOU ----------------
        elif isinstance(ev.metrics, metrics.EOUMetrics):
            turn_metrics[speech_id]["eou_delay"] = ev.metrics.end_of_utterance_delay
            turn_metrics[speech_id]["transcription_delay"] = ev.metrics.transcription_delay
            turn_metrics[speech_id]["on_user_turn_completed_delay"] = ev.metrics.on_user_turn_completed_delay
            turn_metrics[speech_id]["last_speaking_time"] = ev.metrics.last_speaking_time

            SESSION_LOGS.setdefault("eou", []).append({
                "speech_id": speech_id,
                "end_of_utterance_delay": ev.metrics.end_of_utterance_delay,
                "transcription_delay": ev.metrics.transcription_delay,
                "on_user_turn_completed_delay": ev.metrics.on_user_turn_completed_delay,
                "last_speaking_time": ev.metrics.last_speaking_time,
                "timestamp": ev.metrics.timestamp,
            })

        # ---------------- VAD ----------------
        # Commented out cause it clutters the terminal
        elif isinstance(ev.metrics, metrics.VADMetrics):
            logger.info(f"VAD metrics: {ev.metrics.model_dump()}")

        else:
            logger.warning(f"Unknown metrics type: {type(ev.metrics)}")

    # Return collector & cost calculator for later use
    return usage_collector, cost_calc
