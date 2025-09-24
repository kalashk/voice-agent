import json
import logging
from pathlib import Path
from dataclasses import asdict
from datetime import datetime
from helpers.config import LOG_PATH

# Logger for agent/session events
logger = logging.getLogger("agent")


async def log_usage(usage_collector, cost_calc, SESSION_LOGS, SESSION_ID, customer_profile, TTS_PROVIDER, STT_PROVIDER):
    """
    Logs and persists session usage and cost information.
    
    Parameters:
        usage_collector: Aggregates metrics from the session (LLM, STT, TTS)
        cost_calc: CostCalculator instance for computing costs
        SESSION_LOGS: Dict holding detailed logs of transcripts, metrics, and conversation events
        SESSION_ID: Unique identifier for this session
        customer_profile: Dict with customer information
        TTS_PROVIDER: Name of the TTS provider used
        STT_PROVIDER: Name of the STT provider used
    """

    # ------------------------
    # Get usage summary and cost
    # ------------------------
    summary = usage_collector.get_summary()               # Aggregated metrics
    cost_summary = cost_calc.summarize_usage(summary, SESSION_ID)  # Compute costs

    # ------------------------
    # Compute average conversation latency
    # ------------------------
    conversation_latencies = [c["latency_seconds"] for c in SESSION_LOGS.get("conversation", [])]
    avg_latency = sum(conversation_latencies) / len(conversation_latencies) if conversation_latencies else 0.0

    # ------------------------
    # Compute session length in seconds
    # ------------------------
    all_timestamps = []
    for section in ("stt", "tts", "llm", "eou", "conversation"):
        for ev in SESSION_LOGS.get(section, []):
            try:
                # Convert ISO timestamp to datetime object
                all_timestamps.append(datetime.fromisoformat(ev["timestamp"]))
            except Exception:
                # Skip invalid timestamps
                pass

    if all_timestamps:
        session_length = (max(all_timestamps) - min(all_timestamps)).total_seconds()
    else:
        session_length = 0.0

    # ------------------------
    # Log final summaries
    # ------------------------
    logger.info(f"Final Usage: {summary}")
    logger.info(f"Final Cost Summary: {cost_summary}")
    logger.info(f"Average Conversation Latency: {avg_latency:.3f} sec")

    # Convert dataclass summary to dictionary
    usage_dict = asdict(summary)
    usage_dict["session_id"] = SESSION_ID
    usage_dict["average_latency_seconds"] = avg_latency
    usage_dict["session_length_seconds"] = session_length

    # Store metadata in SESSION_LOGS
    SESSION_LOGS["metadata"] = {
        "session_id": SESSION_ID,
        "TTS provider": TTS_PROVIDER,
        "STT provider": STT_PROVIDER,
        "customer_profile": customer_profile,
        "final_usage": usage_dict,
        "final_cost": cost_summary,
    }

    # ------------------------
    # Persist session logs to JSON file
    # ------------------------
    file_path = LOG_PATH / f"{TTS_PROVIDER}_{STT_PROVIDER}_session_{SESSION_ID}.json"
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(SESSION_LOGS, f, indent=2, ensure_ascii=False)
