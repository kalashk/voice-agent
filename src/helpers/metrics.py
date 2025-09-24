from livekit.agents import (
    AgentSession,
    MetricsCollectedEvent,
    metrics,
    UserInputTranscribedEvent,
    ConversationItemAddedEvent,
)
from livekit.agents.llm import ChatMessage
import uuid
import logging
from datetime import timezone, datetime, timedelta
from helpers.usage_tracker import CostCalculator
from helpers.config import TTS_PROVIDER, STT_PROVIDER, IST

logger = logging.getLogger("agent")


#def setup_metrics(session: AgentSession, SESSION_LOGS: dict):
    # usage_collector = metrics.UsageCollector()
    # cost_calc = CostCalculator(stt_provider=STT_PROVIDER, tts_provider=TTS_PROVIDER)

    # turn_metrics = {}  # track metrics per speech_id

    # @session.on("metrics_collected")
    # def _on_metrics_collected(ev: MetricsCollectedEvent):
    #     metrics.log_metrics(ev.metrics)
    #     usage_collector.collect(ev.metrics)
    #     timestamp = datetime.now(IST).isoformat()

    #     speech_id = getattr(ev.metrics, "speech_id", str(uuid.uuid4()))
    #     turn_metrics.setdefault(speech_id, {})

    #     # STT Metrics
    #     if isinstance(ev.metrics, metrics.STTMetrics):
    #         SESSION_LOGS.setdefault("stt", []).append({
    #             "speech_id": speech_id,
    #             "audio_duration": ev.metrics.audio_duration,
    #             "duration": getattr(ev.metrics, "duration", 0.0),
    #             "streamed": getattr(ev.metrics, "streamed", False),
    #             "timestamp": timestamp,
    #         })
    #         turn_metrics[speech_id]["stt_seconds"] = ev.metrics.audio_duration

    #     # LLM Metrics
    #     elif isinstance(ev.metrics, metrics.LLMMetrics):
    #         SESSION_LOGS.setdefault("llm", []).append({
    #             "speech_id": speech_id,
    #             "duration": ev.metrics.duration,
    #             "completion_tokens": ev.metrics.completion_tokens,
    #             "prompt_tokens": ev.metrics.prompt_tokens,
    #             "prompt_cached_tokens": ev.metrics.prompt_cached_tokens,
    #             "total_tokens": ev.metrics.total_tokens,
    #             "tokens_per_second": ev.metrics.tokens_per_second,
    #             "ttft": ev.metrics.ttft,
    #             "timestamp": timestamp,
    #         })
    #         turn_metrics[speech_id]["llm_ttft"] = ev.metrics.ttft

    #     # TTS Metrics
    #     elif isinstance(ev.metrics, metrics.TTSMetrics):
    #         SESSION_LOGS.setdefault("tts", []).append({
    #             "speech_id": speech_id,
    #             "audio_duration": ev.metrics.audio_duration,
    #             "characters_count": ev.metrics.characters_count,
    #             "duration": ev.metrics.duration,
    #             "ttfb": ev.metrics.ttfb,
    #             "streamed": getattr(ev.metrics, "streamed", False),
    #             "timestamp": timestamp,
    #         })
    #         turn_metrics[speech_id]["tts_ttfb"] = ev.metrics.ttfb

    #     # EOU Metrics
    #     elif isinstance(ev.metrics, metrics.EOUMetrics):
    #         turn_metrics[speech_id]["eou_delay"] = ev.metrics.end_of_utterance_delay
    #         turn_metrics[speech_id]["transcription_delay"] = getattr(ev.metrics, "transcription_delay", 0.0)
    #         turn_metrics[speech_id]["on_user_turn_completed_delay"] = getattr(ev.metrics, "on_user_turn_completed_delay", 0.0)

    #         SESSION_LOGS.setdefault("eou", []).append({
    #             "speech_id": speech_id,
    #             "end_of_utterance_delay": ev.metrics.end_of_utterance_delay,
    #             "transcription_delay": getattr(ev.metrics, "transcription_delay", 0.0),
    #             "on_user_turn_completed_delay": getattr(ev.metrics, "on_user_turn_completed_delay", 0.0),
    #             "timestamp": timestamp,
    #         })

    #     # VAD Metrics
    #     elif isinstance(ev.metrics, metrics.VADMetrics):
    #         logger.info(f"VAD metrics: {ev.metrics.model_dump()}")
    #     else:
    #         logger.warning(f"Unknown metrics type: {type(ev.metrics)}")

    #     # --- Compute conversation latency per speech_id ---
    #     for sid, m in list(turn_metrics.items()):
    #         if all(k in m for k in ("eou_delay", "llm_ttft", "tts_ttfb")):
    #             total_latency = m["eou_delay"] + m["llm_ttft"] + m["tts_ttfb"]
    #             SESSION_LOGS.setdefault("conversation", []).append({
    #                 "speech_id": sid,
    #                 "latency_seconds": total_latency,
    #                 "stt_seconds": m.get("stt_seconds", 0.0),
    #                 "llm_ttft": m["llm_ttft"],
    #                 "tts_ttfb": m["tts_ttfb"],
    #                 "eou_delay": m["eou_delay"],
    #                 "transcription_delay": m.get("transcription_delay", 0.0),
    #                 "on_user_turn_completed_delay": m.get("on_user_turn_completed_delay", 0.0),
    #                 "timestamp": timestamp,
    #             })
    #             del turn_metrics[sid]

    # return usage_collector, cost_calc

def setup_metrics(session: AgentSession, SESSION_LOGS: dict):
    """
    Sets up real-time metrics collection for a LiveKit AgentSession.
    Tracks LLM, STT, TTS, EOU, VAD, and conversation latencies.
    Stores detailed event logs in SESSION_LOGS and returns:
      - usage_collector: aggregates usage metrics
      - cost_calc: cost calculator for billing
    """

    # Initialize a usage collector (aggregates metrics across session)
    usage_collector = metrics.UsageCollector()

    # Initialize a cost calculator using global STT/TTS providers
    cost_calc = CostCalculator(stt_provider=STT_PROVIDER, tts_provider=TTS_PROVIDER)

    # Track metrics per individual speech segment
    turn_metrics = {}  # {speech_id: {stt_seconds, llm_ttft, tts_ttfb, eou_delay, ...}}

    # ------------------------
    # Capture live/final user transcripts
    # ------------------------
    @session.on("user_input_transcribed")
    def _on_user_transcribed(ev: UserInputTranscribedEvent):
        timestamp = datetime.now(IST).isoformat()
        SESSION_LOGS.setdefault("transcript", []).append({
            "speech_id": ev.speaker_id or str(uuid.uuid4()),  # assign id if missing
            "role": "user",
            "text": ev.transcript.strip(),
            "is_final": ev.is_final,       # True if this is final transcription
            "language": ev.language,
            "timestamp": timestamp,
        })

    # ------------------------
    # Capture conversation items (messages from assistant or user)
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
                    "interrupted": ev.item.interrupted,           # was the message interrupted mid-generation
                    "confidence": ev.item.transcript_confidence,  # optional speech confidence
                    "timestamp": timestamp,
                })

    # ------------------------
    # Capture per-component metrics
    # ------------------------
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        """
        Handles metrics events for STT, LLM, TTS, EOU, VAD, etc.
        Updates SESSION_LOGS and aggregates per-turn metrics for latency calculations.
        """
        # Log raw metrics for debugging
        metrics.log_metrics(ev.metrics)

        # Collect metrics into the usage_collector for overall summary
        usage_collector.collect(ev.metrics)

        timestamp = datetime.now(IST).isoformat()
        speech_id = getattr(ev.metrics, "speech_id", str(uuid.uuid4()))
        turn_metrics.setdefault(speech_id, {})

        # ------------------------ STT Metrics ------------------------
        if isinstance(ev.metrics, metrics.STTMetrics):
            SESSION_LOGS.setdefault("stt", []).append({
                "speech_id": speech_id,
                "audio_duration": ev.metrics.audio_duration,
                "duration": getattr(ev.metrics, "duration", 0.0),
                "streamed": getattr(ev.metrics, "streamed", False),
                "timestamp": timestamp,
            })
            turn_metrics[speech_id]["stt_seconds"] = ev.metrics.audio_duration

        # ------------------------ LLM Metrics ------------------------
        elif isinstance(ev.metrics, metrics.LLMMetrics):
            SESSION_LOGS.setdefault("llm", []).append({
                "speech_id": speech_id,
                "duration": ev.metrics.duration,
                "completion_tokens": ev.metrics.completion_tokens,
                "prompt_tokens": ev.metrics.prompt_tokens,
                "prompt_cached_tokens": ev.metrics.prompt_cached_tokens,
                "total_tokens": ev.metrics.total_tokens,
                "tokens_per_second": ev.metrics.tokens_per_second,
                "ttft": ev.metrics.ttft,   # time to first token
                "timestamp": timestamp,
            })
            turn_metrics[speech_id]["llm_ttft"] = ev.metrics.ttft

        # ------------------------ TTS Metrics ------------------------
        elif isinstance(ev.metrics, metrics.TTSMetrics):
            SESSION_LOGS.setdefault("tts", []).append({
                "speech_id": speech_id,
                "audio_duration": ev.metrics.audio_duration,
                "characters_count": ev.metrics.characters_count,
                "duration": ev.metrics.duration,
                "ttfb": ev.metrics.ttfb,   # time to first byte
                "streamed": getattr(ev.metrics, "streamed", False),
                "timestamp": timestamp,
            })
            turn_metrics[speech_id]["tts_ttfb"] = ev.metrics.ttfb

        # ------------------------ End-of-Utterance Metrics ------------------------
        elif isinstance(ev.metrics, metrics.EOUMetrics):
            turn_metrics[speech_id]["eou_delay"] = ev.metrics.end_of_utterance_delay
            turn_metrics[speech_id]["transcription_delay"] = getattr(ev.metrics, "transcription_delay", 0.0)
            turn_metrics[speech_id]["on_user_turn_completed_delay"] = getattr(ev.metrics, "on_user_turn_completed_delay", 0.0)

            SESSION_LOGS.setdefault("eou", []).append({
                "speech_id": speech_id,
                "end_of_utterance_delay": ev.metrics.end_of_utterance_delay,
                "transcription_delay": getattr(ev.metrics, "transcription_delay", 0.0),
                "on_user_turn_completed_delay": getattr(ev.metrics, "on_user_turn_completed_delay", 0.0),
                "timestamp": timestamp,
            })

        # ------------------------ VAD Metrics ------------------------
        elif isinstance(ev.metrics, metrics.VADMetrics):
            logger.info(f"VAD metrics: {ev.metrics.model_dump()}")

        else:
            logger.warning(f"Unknown metrics type: {type(ev.metrics)}")

        # ------------------------
        # Compute conversation latency per speech_id
        # ------------------------
        for sid, m in list(turn_metrics.items()):
            # Only calculate if all relevant metrics are available
            if all(k in m for k in ("eou_delay", "llm_ttft", "tts_ttfb")):
                total_latency = m["eou_delay"] + m["llm_ttft"] + m["tts_ttfb"]
                SESSION_LOGS.setdefault("conversation", []).append({
                    "speech_id": sid,
                    "latency_seconds": total_latency,
                    "stt_seconds": m.get("stt_seconds", 0.0),
                    "llm_ttft": m["llm_ttft"],
                    "tts_ttfb": m["tts_ttfb"],
                    "eou_delay": m["eou_delay"],
                    "transcription_delay": m.get("transcription_delay", 0.0),
                    "on_user_turn_completed_delay": m.get("on_user_turn_completed_delay", 0.0),
                    "timestamp": timestamp,
                })
                # remove completed entry to free memory
                del turn_metrics[sid]

    # Return collector & cost calculator for later use
    return usage_collector, cost_calc
