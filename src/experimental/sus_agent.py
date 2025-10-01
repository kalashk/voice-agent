import asyncio
import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterable, Optional, List

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import (
    Agent,
    AgentSession,
    ChatContext,
    ChatMessage,
    FunctionTool,
    MetricsCollectedEvent,
    ModelSettings,
    RoomInputOptions,
    RunContext,
    metrics,
    stt,
)
from livekit.agents.llm.tool_context import RawFunctionTool
from livekit.plugins import sarvam, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(".env.local")

# Configure minimal console logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class StructuredMetricsLogger:
    """Logs metrics to structured JSON files for easy analysis."""
    
    def __init__(self, output_dir: str = "metrics_logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Generate unique session ID
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_start = time.time()
        
        # Data structures for different metric types
        self.component_timings = defaultdict(list)
        self.pipeline_stages = []
        self.agent_metrics = {
            "stt": [],
            "llm": [],
            "tts": [],
            "vad": [],
            "eou": []
        }
        self.conversation_turns = []
        self.usage_collector = metrics.UsageCollector()
        
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Metrics will be saved to: {self.output_dir}")
        
    def log_component_timing(self, component: str, operation: str, 
                            duration: float, metadata: dict = {}):
        """Log timing for a specific component operation."""
        self.component_timings[component].append({
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": time.time() - self.session_start,
            "metadata": metadata or {}
        })
        
    def log_pipeline_stage(self, stage: str, details: dict = {}):
        """Log a pipeline lifecycle stage."""
        self.pipeline_stages.append({
            "stage": stage,
            "timestamp": time.time() - self.session_start,
            "details": details or {}
        })
        
    def log_stt_metrics(self, metric: metrics.STTMetrics):
        """Log STT-specific metrics."""
        self.agent_metrics["stt"].append({
            "timestamp": metric.timestamp - self.session_start,
            "duration_ms": round(metric.duration * 1000, 2),
            "audio_duration_s": round(metric.audio_duration, 2),
            "streamed": metric.streamed,
            "label": metric.label,
            "request_id": metric.request_id
        })
        
    def log_llm_metrics(self, metric: metrics.LLMMetrics):
        """Log LLM-specific metrics."""
        self.agent_metrics["llm"].append({
            "timestamp": metric.timestamp - self.session_start,
            "duration_ms": round(metric.duration * 1000, 2),
            "ttft_ms": round(metric.ttft * 1000, 2),
            "completion_tokens": metric.completion_tokens,
            "prompt_tokens": metric.prompt_tokens,
            "cached_tokens": metric.prompt_cached_tokens,
            "total_tokens": metric.total_tokens,
            "tokens_per_second": round(metric.tokens_per_second, 2),
            "cancelled": metric.cancelled,
            "speech_id": metric.speech_id
        })
        
    def log_tts_metrics(self, metric: metrics.TTSMetrics):
        """Log TTS-specific metrics."""
        self.agent_metrics["tts"].append({
            "timestamp": metric.timestamp - self.session_start,
            "duration_ms": round(metric.duration * 1000, 2),
            "ttfb_ms": round(metric.ttfb * 1000, 2),
            "audio_duration_s": round(metric.audio_duration, 2),
            "characters": metric.characters_count,
            "streamed": metric.streamed,
            "cancelled": metric.cancelled,
            "speech_id": metric.speech_id
        })
        
    def log_vad_metrics(self, metric: metrics.VADMetrics):
        """Log VAD-specific metrics."""
        self.agent_metrics["vad"].append({
            "timestamp": metric.timestamp - self.session_start,
            "idle_time_ms": round(metric.idle_time * 1000, 2),
            "inference_duration_ms": round(metric.inference_duration_total * 1000, 2),
            "inference_count": metric.inference_count,
            "label": metric.label
        })
        
    def log_eou_metrics(self, metric: metrics.EOUMetrics):
        """Log end-of-utterance metrics."""
        total_latency = (
            metric.end_of_utterance_delay + 
            metric.transcription_delay + 
            metric.on_user_turn_completed_delay
        )
        
        eou_data = {
            "timestamp": metric.timestamp - self.session_start,
            "total_latency_ms": round(total_latency * 1000, 2),
            "eou_delay_ms": round(metric.end_of_utterance_delay * 1000, 2),
            "transcription_delay_ms": round(metric.transcription_delay * 1000, 2),
            "callback_delay_ms": round(metric.on_user_turn_completed_delay * 1000, 2),
            "speech_id": metric.speech_id
        }
        
        self.agent_metrics["eou"].append(eou_data)
        
        # Also track as conversation turn
        self.conversation_turns.append(eou_data)
        
    def collect_agent_metrics(self, ev: MetricsCollectedEvent):
        """Collect and route metrics to appropriate handlers."""
        metric = ev.metrics
        self.usage_collector.collect(metric)
        
        if isinstance(metric, metrics.STTMetrics):
            self.log_stt_metrics(metric)
        elif isinstance(metric, metrics.LLMMetrics):
            self.log_llm_metrics(metric)
        elif isinstance(metric, metrics.TTSMetrics):
            self.log_tts_metrics(metric)
        elif isinstance(metric, metrics.VADMetrics):
            self.log_vad_metrics(metric)
        elif isinstance(metric, metrics.EOUMetrics):
            self.log_eou_metrics(metric)
            
    def calculate_statistics(self) -> dict:
        """Calculate statistical summaries for all components."""
        stats = {}
        
        for component, timings in self.component_timings.items():
            if not timings:
                continue
                
            durations = [t["duration_ms"] for t in timings]
            stats[component] = {
                "count": len(durations),
                "total_ms": round(sum(durations), 2),
                "avg_ms": round(sum(durations) / len(durations), 2),
                "min_ms": round(min(durations), 2),
                "max_ms": round(max(durations), 2),
                "p50_ms": round(sorted(durations)[len(durations)//2], 2),
                "p95_ms": round(sorted(durations)[int(len(durations)*0.95)], 2) if len(durations) > 1 else round(durations[0], 2)
            }
            
        return stats
        
    def calculate_conversation_latency_stats(self) -> dict:
        """Calculate statistics for conversation latency."""
        if not self.conversation_turns:
            return {}
            
        latencies = [turn["total_latency_ms"] for turn in self.conversation_turns]
        return {
            "turns": len(latencies),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "min_latency_ms": round(min(latencies), 2),
            "max_latency_ms": round(max(latencies), 2),
            "p50_latency_ms": round(sorted(latencies)[len(latencies)//2], 2),
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies)*0.95)], 2) if len(latencies) > 1 else round(latencies[0], 2)
        }
        
    # def save_all_metrics(self):
    #     """Save all metrics to JSON files."""
    #     session_dir = self.output_dir / self.session_id
    #     session_dir.mkdir(exist_ok=True)
        
    #     # 1. Summary Report - Most important file
    #     summary = {
    #         "session_id": self.session_id,
    #         "total_duration_s": round(time.time() - self.session_start, 2),
    #         "component_statistics": self.calculate_statistics(),
    #         "conversation_latency": self.calculate_conversation_latency_stats(),
    #         "usage_summary": self.usage_collector.get_summary(),
    #         "component_breakdown": self._get_component_breakdown()
    #     }
        
    #     with open(session_dir / "summary.json", "w") as f:
    #         json.dump(summary, f, indent=2)
            
    #     # 2. Detailed Component Timings
    #     with open(session_dir / "component_timings.json", "w") as f:
    #         json.dump(dict(self.component_timings), f, indent=2)
            
    #     # 3. Agent Metrics (STT, LLM, TTS, VAD, EOU)
    #     with open(session_dir / "agent_metrics.json", "w") as f:
    #         json.dump(self.agent_metrics, f, indent=2)
            
    #     # 4. Pipeline Stages
    #     with open(session_dir / "pipeline_stages.json", "w") as f:
    #         json.dump(self.pipeline_stages, f, indent=2)
            
    #     # 5. Conversation Turns
    #     with open(session_dir / "conversation_turns.json", "w") as f:
    #         json.dump(self.conversation_turns, f, indent=2)
            
    #     logger.info(f"\nMetrics saved to: {session_dir}")
    #     logger.info(f"  - summary.json (START HERE)")
    #     logger.info(f"  - component_timings.json")
    #     logger.info(f"  - agent_metrics.json")
    #     logger.info(f"  - pipeline_stages.json")
    #     logger.info(f"  - conversation_turns.json")
        
    def save_all_metrics(self):
        """Save all metrics into a single JSON file in the current working directory."""
        session_file = Path(f"{self.session_id}_metrics.json")
        summary_obj = self.usage_collector.get_summary()

        all_metrics = {
            "session_id": self.session_id,
            "total_duration_s": round(time.time() - self.session_start, 2),

            # summaries
            "component_statistics": self.calculate_statistics(),
            "conversation_latency": self.calculate_conversation_latency_stats(),
            "usage_summary": summary_obj.__dict__,
            "component_breakdown": self._get_component_breakdown(),

            # raw data
            "component_timings": dict(self.component_timings),
            "agent_metrics": self.agent_metrics,
            "pipeline_stages": self.pipeline_stages,
            "conversation_turns": self.conversation_turns,
        }

        with open(session_file, "w") as f:
            json.dump(all_metrics, f, indent=2)

        logger.info(f"\n✅ Metrics saved to {session_file.absolute()}")

    def _get_component_breakdown(self) -> dict:
        """Get time breakdown by component for quick analysis."""
        breakdown = {}
        
        for component, stats in self.calculate_statistics().items():
            breakdown[component] = {
                "total_time_ms": stats["total_ms"],
                "percentage": 0.0,  # Will calculate after
                "avg_per_operation_ms": stats["avg_ms"],
                "operation_count": stats["count"]
            }
            
        # Calculate percentages
        total_time = sum(b["total_time_ms"] for b in breakdown.values())
        if total_time > 0:
            for component in breakdown:
                breakdown[component]["percentage"] = round(
                    (breakdown[component]["total_time_ms"] / total_time) * 100, 2
                )
                
        return dict(sorted(breakdown.items(), 
                          key=lambda x: x[1]["total_time_ms"], 
                          reverse=True))


class MonitoredAssistant(Agent):
    """Agent with detailed monitoring at every pipeline stage."""
    
    def __init__(self, metrics_logger: StructuredMetricsLogger) -> None:
        super().__init__(instructions="You are a podcast host, here to do a podcast")
        self.metrics_logger = metrics_logger
        
    async def on_enter(self):
        start_time = time.time()
        self.metrics_logger.log_pipeline_stage("agent_enter")
        await super().on_enter()
        self.metrics_logger.log_component_timing("agent_lifecycle", "on_enter", 
                                                  time.time() - start_time)
        
    async def on_exit(self):
        start_time = time.time()
        self.metrics_logger.log_pipeline_stage("agent_exit")
        await super().on_exit()
        self.metrics_logger.log_component_timing("agent_lifecycle", "on_exit", 
                                                  time.time() - start_time)
        
    async def on_user_turn_completed(
        self, turn_ctx: ChatContext, new_message: ChatMessage
    ) -> None:
        start_time = time.time()
        message_text = new_message.text_content or ""
        
        self.metrics_logger.log_pipeline_stage(
            "user_turn_completed",
            {"message_length": len(message_text)}
        )
        
        await super().on_user_turn_completed(turn_ctx, new_message)
        
        self.metrics_logger.log_component_timing(
            "agent_lifecycle", 
            "on_user_turn_completed", 
            time.time() - start_time,
            {"message_length": len(message_text)}
        )
        
    async def stt_node(
        self, audio: AsyncIterable[rtc.AudioFrame], model_settings: ModelSettings
    ) -> Optional[AsyncIterable[stt.SpeechEvent]]:
        start_time = time.time()
        frame_count = 0
        total_audio_duration = 0.0
        
        self.metrics_logger.log_pipeline_stage("stt_start")
        
        async def monitored_audio():
            nonlocal frame_count, total_audio_duration
            async for frame in audio:
                frame_count += 1
                total_audio_duration += frame.samples_per_channel / frame.sample_rate
                yield frame
                
        events = Agent.default.stt_node(self, monitored_audio(), model_settings)
        
        async def monitored_events():
            event_count = 0
            async for event in events:
                event_count += 1
                yield event
                
            self.metrics_logger.log_component_timing(
                "stt_pipeline",
                "complete",
                time.time() - start_time,
                {
                    "frame_count": frame_count,
                    "event_count": event_count,
                    "audio_duration_s": round(total_audio_duration, 2)
                }
            )
            
        return monitored_events()
        
    async def llm_node(
        self,
        chat_ctx: ChatContext,
        tools: List[FunctionTool | RawFunctionTool],
        model_settings: ModelSettings
    ) -> AsyncIterable[Any]:
        start_time = time.time()
        
        context_info = {
            "message_count": len(chat_ctx.items),
            "tool_count": len(tools)
        }
        self.metrics_logger.log_pipeline_stage("llm_start", context_info)
        
        chunk_count = 0
        first_chunk_time = None
        
        async for chunk in Agent.default.llm_node(
            self, chat_ctx, tools=tools, model_settings=model_settings
        ):
            if first_chunk_time is None:
                first_chunk_time = time.time()
                self.metrics_logger.log_component_timing(
                    "llm_pipeline",
                    "time_to_first_chunk",
                    first_chunk_time - start_time,
                    context_info
                )
                
            chunk_count += 1
            yield chunk
            
        self.metrics_logger.log_component_timing(
            "llm_pipeline",
            "complete",
            time.time() - start_time,
            {**context_info, "chunk_count": chunk_count}
        )
        
    async def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        start_time = time.time()
        self.metrics_logger.log_pipeline_stage("tts_start")
        
        text_chunks = []
        async def monitored_text():
            async for chunk in text:
                text_chunks.append(chunk)
                yield chunk
                
        frame_count = 0
        first_frame_time = None
        total_audio_duration = 0.0
        
        async for frame in Agent.default.tts_node(self, monitored_text(), model_settings):
            if first_frame_time is None:
                first_frame_time = time.time()
                self.metrics_logger.log_component_timing(
                    "tts_pipeline",
                    "time_to_first_byte",
                    first_frame_time - start_time,
                    {"text_length": sum(len(c) for c in text_chunks)}
                )
                
            frame_count += 1
            total_audio_duration += frame.samples_per_channel / frame.sample_rate
            yield frame
            
        self.metrics_logger.log_component_timing(
            "tts_pipeline",
            "complete",
            time.time() - start_time,
            {
                "frame_count": frame_count,
                "text_length": len(''.join(text_chunks)),
                "audio_duration_s": round(total_audio_duration, 2)
            }
        )


async def entrypoint(ctx: agents.JobContext):
    logger.info("Starting Voice Agent with Structured Metrics Logging")
    
    # Initialize metrics logger
    metrics_logger = StructuredMetricsLogger(output_dir="metrics_logs")
    
    # Track initialization times
    init_start = time.time()
    
    logger.info("Initializing components...")
    
    stt_start = time.time()
    stt_instance = sarvam.STT(language="en-IN", model="saarika:v2.5")
    metrics_logger.log_component_timing("initialization", "stt", time.time() - stt_start)
    
    llm_start = time.time()
    llm_instance = openai.LLM(model="gpt-4o-mini")
    metrics_logger.log_component_timing("initialization", "llm", time.time() - llm_start)
    
    tts_start = time.time()
    tts_instance = sarvam.TTS(target_language_code="en-IN", speaker="anushka")
    metrics_logger.log_component_timing("initialization", "tts", time.time() - tts_start)
    
    vad_start = time.time()
    vad_instance = silero.VAD.load(
        min_speech_duration=0.05,        # detect speech after 50ms
        min_silence_duration=0.2,        # quicker stop after 200ms silence (default is 0.4s)
        prefix_padding_duration=0.2,     # keep only 200ms padding before speech
        max_buffered_speech=30.0,        # smaller buffer for responsiveness
        activation_threshold=0.4,        # lower threshold for earlier detection of speech start
        sample_rate=16000,
        force_cpu=True
    )
    metrics_logger.log_component_timing("initialization", "vad", time.time() - vad_start)
    
    td_start = time.time()
    turn_detector = MultilingualModel()
    metrics_logger.log_component_timing("initialization", "turn_detection", time.time() - td_start)
    
    metrics_logger.log_component_timing("initialization", "total", time.time() - init_start)
    logger.info(f"Components initialized in {(time.time() - init_start)*1000:.0f}ms")
    
    # Create session
    session_start = time.time()
    session = AgentSession(
        stt=stt_instance,
        llm=llm_instance,
        tts=tts_instance,
        vad=vad_instance,
        turn_detection=turn_detector,
    )
    
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics_logger.collect_agent_metrics(ev)
    
    metrics_logger.log_component_timing("initialization", "session", time.time() - session_start)
    
    # Start session
    logger.info("Starting agent session...")
    start_time = time.time()
    await session.start(
        room=ctx.room,
        agent=MonitoredAssistant(metrics_logger),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    metrics_logger.log_component_timing("session", "start", time.time() - start_time)
    
    # Generate initial greeting
    greeting_start = time.time()
    await session.generate_reply(instructions="Greet the candidate")
    metrics_logger.log_component_timing("session", "initial_greeting", time.time() - greeting_start)
    
    # Setup shutdown callback
    async def save_metrics():
        logger.info("\nSaving metrics...")
        metrics_logger.save_all_metrics()
        logger.info("Metrics saved successfully!")
        
    ctx.add_shutdown_callback(save_metrics)
    
    logger.info("Agent is ready!")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))