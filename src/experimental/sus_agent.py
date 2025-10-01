import asyncio
import json
import logging
import time
from collections import defaultdict
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

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DetailedMetricsCollector:
    """Collects and analyzes detailed metrics from all pipeline components."""
    
    def __init__(self):
        self.usage_collector = metrics.UsageCollector()
        self.custom_timings = defaultdict(list)
        self.pipeline_events = []
        
    def log_timing(self, component: str, operation: str, duration: float, metadata: dict = {}):
        """Log custom timing data for any operation."""
        timing_data = {
            "timestamp": time.time(),
            "component": component,
            "operation": operation,
            "duration_ms": duration * 1000,
            "metadata": metadata or {}
        }
        self.custom_timings[component].append(timing_data)
        logger.info(
            f"⏱️  [{component}] {operation}: {duration*1000:.2f}ms "
            f"{json.dumps(metadata) if metadata else ''}"
        )
        
    def log_pipeline_event(self, event: str, details: dict = {}):
        """Log pipeline lifecycle events."""
        event_data = {
            "timestamp": time.time(),
            "event": event,
            "details": details or {}
        }
        self.pipeline_events.append(event_data)
        logger.info(f"📍 Pipeline Event: {event} {json.dumps(details) if details else ''}")
        
    def collect_agent_metrics(self, ev: MetricsCollectedEvent):
        """Collect metrics from the agent session."""
        metric = ev.metrics
        self.usage_collector.collect(metric)
        
        # Log detailed metrics based on type
        if isinstance(metric, metrics.STTMetrics):
            logger.info(
                f"🎤 STT Metrics - Duration: {metric.duration*1000:.2f}ms, "
                f"Audio: {metric.audio_duration:.2f}s, Streamed: {metric.streamed}, "
                f"Label: {metric.label}, RequestID: {metric.request_id}"
            )
            
        elif isinstance(metric, metrics.LLMMetrics):
            logger.info(
                f"🧠 LLM Metrics - Duration: {metric.duration*1000:.2f}ms, "
                f"TTFT: {metric.ttft*1000:.2f}ms, Tokens/s: {metric.tokens_per_second:.2f}, "
                f"Completion: {metric.completion_tokens}, Prompt: {metric.prompt_tokens}, "
                f"Cached: {metric.prompt_cached_tokens}, Cancelled: {metric.cancelled}, "
                f"SpeechID: {metric.speech_id}"
            )
            
        elif isinstance(metric, metrics.TTSMetrics):
            logger.info(
                f"🔊 TTS Metrics - Duration: {metric.duration*1000:.2f}ms, "
                f"TTFB: {metric.ttfb*1000:.2f}ms, Audio: {metric.audio_duration:.2f}s, "
                f"Characters: {metric.characters_count}, Streamed: {metric.streamed}, "
                f"Cancelled: {metric.cancelled}, SpeechID: {metric.speech_id}"
            )
            
        elif isinstance(metric, metrics.VADMetrics):
            logger.info(
                f"🔇 VAD Metrics - Idle: {metric.idle_time*1000:.2f}ms, "
                f"Inference Total: {metric.inference_duration_total*1000:.2f}ms, "
                f"Count: {metric.inference_count}"
            )
            
        elif isinstance(metric, metrics.EOUMetrics):
            total_latency = (
                metric.end_of_utterance_delay + 
                metric.transcription_delay + 
                metric.on_user_turn_completed_delay
            )
            logger.info(
                f"⏹️  EOU Metrics - Total: {total_latency*1000:.2f}ms, "
                f"EOU Delay: {metric.end_of_utterance_delay*1000:.2f}ms, "
                f"Transcription: {metric.transcription_delay*1000:.2f}ms, "
                f"Callback: {metric.on_user_turn_completed_delay*1000:.2f}ms, "
                f"Last Speaking: {metric.last_speaking_time}, SpeechID: {metric.speech_id}"
            )
            
    def get_summary(self) -> dict:
        """Get a comprehensive summary of all collected metrics."""
        summary = {
            "usage": self.usage_collector.get_summary(),
            "custom_timings": dict(self.custom_timings),
            "pipeline_events": self.pipeline_events,
            "statistics": self._calculate_statistics()
        }
        return summary
        
    def _calculate_statistics(self) -> dict:
        """Calculate statistical summaries of custom timings."""
        stats = {}
        for component, timings in self.custom_timings.items():
            if timings:
                durations = [t["duration_ms"] for t in timings]
                stats[component] = {
                    "count": len(durations),
                    "total_ms": sum(durations),
                    "avg_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                }
        return stats


class MonitoredAssistant(Agent):
    """Agent with detailed monitoring at every pipeline stage."""
    
    def __init__(self, metrics_collector: DetailedMetricsCollector) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant made to take users information and try to sell them quick loan based on the information you got")
        self.metrics_collector = metrics_collector
        
    async def on_enter(self):
        """Called when agent becomes active."""
        start_time = time.time()
        self.metrics_collector.log_pipeline_event("agent_enter")
        
        await super().on_enter()
        
        duration = time.time() - start_time
        self.metrics_collector.log_timing("agent_lifecycle", "on_enter", duration)
        
    async def on_exit(self):
        """Called before agent gives control to another agent."""
        start_time = time.time()
        self.metrics_collector.log_pipeline_event("agent_exit")
        
        await super().on_exit()
        
        duration = time.time() - start_time
        self.metrics_collector.log_timing("agent_lifecycle", "on_exit", duration)
        
    async def on_user_turn_completed(
        self, turn_ctx: ChatContext, new_message: ChatMessage
    ) -> None:
        """Called when user's turn ends, before agent reply."""
        start_time = time.time()
        
        message_text = new_message.text_content or ""
        self.metrics_collector.log_pipeline_event(
            "user_turn_completed",
            {"message_length": len(message_text), "role": new_message.role}
        )
        logger.debug(f"💬 User message: {message_text[:100]}...")
        
        await super().on_user_turn_completed(turn_ctx, new_message)
        
        duration = time.time() - start_time
        self.metrics_collector.log_timing(
            "agent_lifecycle", 
            "on_user_turn_completed", 
            duration,
            {"message_length": len(message_text)}
        )
        
    async def stt_node(
        self, audio: AsyncIterable[rtc.AudioFrame], model_settings: ModelSettings
    ) -> Optional[AsyncIterable[stt.SpeechEvent]]:
        """Monitor STT processing."""
        start_time = time.time()
        frame_count = 0
        total_audio_duration = 0.0
        
        self.metrics_collector.log_pipeline_event("stt_start")
        
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
                if hasattr(event, 'type'):
                    logger.debug(f"🎤 STT Event: {event.type}")
                yield event
                
            duration = time.time() - start_time
            self.metrics_collector.log_timing(
                "stt_pipeline",
                "complete",
                duration,
                {
                    "frame_count": frame_count,
                    "event_count": event_count,
                    "audio_duration_s": total_audio_duration
                }
            )
            self.metrics_collector.log_pipeline_event(
                "stt_complete",
                {"frame_count": frame_count, "audio_duration_s": total_audio_duration}
            )
            
        return monitored_events()
        
    async def llm_node(
        self,
        chat_ctx: ChatContext,
        tools: List[FunctionTool | RawFunctionTool],
        model_settings: ModelSettings
    ) -> AsyncIterable[Any]:
        """Monitor LLM processing."""
        start_time = time.time()
        
        context_info = {
            "message_count": len(chat_ctx.items),
            "tool_count": len(tools)
        }
        self.metrics_collector.log_pipeline_event("llm_start", context_info)
        
        chunk_count = 0
        first_chunk_time = None
        
        async for chunk in Agent.default.llm_node(
            self, 
            chat_ctx, 
            tools = tools, 
            model_settings= model_settings,
        ):
            if first_chunk_time is None:
                first_chunk_time = time.time()
                ttft = first_chunk_time - start_time
                self.metrics_collector.log_timing(
                    "llm_pipeline",
                    "time_to_first_chunk",
                    ttft,
                    context_info
                )
                
            chunk_count += 1
            yield chunk
            
        duration = time.time() - start_time
        self.metrics_collector.log_timing(
            "llm_pipeline",
            "complete",
            duration,
            {**context_info, "chunk_count": chunk_count}
        )
        self.metrics_collector.log_pipeline_event("llm_complete", {"chunk_count": chunk_count})
        
    async def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        """Monitor TTS processing."""
        start_time = time.time()
        
        self.metrics_collector.log_pipeline_event("tts_start")
        
        text_chunks = []
        async def monitored_text():
            async for chunk in text:
                text_chunks.append(chunk)
                logger.debug(f"🔊 TTS Input: {chunk[:50]}...")
                yield chunk
                
        frame_count = 0
        first_frame_time = None
        total_audio_duration = 0.0
        
        async for frame in Agent.default.tts_node(self, monitored_text(), model_settings):
            if first_frame_time is None:
                first_frame_time = time.time()
                ttfb = first_frame_time - start_time
                self.metrics_collector.log_timing(
                    "tts_pipeline",
                    "time_to_first_byte",
                    ttfb,
                    {"text_length": sum(len(c) for c in text_chunks)}
                )
                
            frame_count += 1
            total_audio_duration += frame.samples_per_channel / frame.sample_rate
            yield frame
            
        duration = time.time() - start_time
        total_text = ''.join(text_chunks)
        self.metrics_collector.log_timing(
            "tts_pipeline",
            "complete",
            duration,
            {
                "frame_count": frame_count,
                "text_length": len(total_text),
                "audio_duration_s": total_audio_duration
            }
        )
        self.metrics_collector.log_pipeline_event(
            "tts_complete",
            {"frame_count": frame_count, "audio_duration_s": total_audio_duration}
        )


async def entrypoint(ctx: agents.JobContext):
    """Main entry point with comprehensive monitoring."""
    logger.info("=" * 80)
    logger.info("🚀 Starting Voice Agent with Detailed Metrics")
    logger.info("=" * 80)
    
    # Initialize metrics collector
    metrics_collector = DetailedMetricsCollector()
    
    # Track component initialization times
    init_start = time.time()
    
    logger.info("🔧 Initializing STT...")
    stt_start = time.time()
    stt_instance = sarvam.STT(
            language="hi-IN",
            model="saarika:v2.5"
        )
    metrics_collector.log_timing("initialization", "stt", time.time() - stt_start)
    
    logger.info("🔧 Initializing LLM...")
    llm_start = time.time()
    llm_instance = openai.LLM(model="gpt-4o-mini")
    metrics_collector.log_timing("initialization", "llm", time.time() - llm_start)
    
    logger.info("🔧 Initializing TTS...")
    tts_start = time.time()
    tts_instance = sarvam.TTS(
            target_language_code="hi-IN",
            speaker="anushka",
            #enable_preprocessing=True,
        )
    metrics_collector.log_timing("initialization", "tts", time.time() - tts_start)
    
    logger.info("🔧 Initializing VAD...")
    vad_start = time.time()
    vad_instance = silero.VAD.load()
    metrics_collector.log_timing("initialization", "vad", time.time() - vad_start)
    
    logger.info("🔧 Initializing Turn Detection...")
    td_start = time.time()
    turn_detector = MultilingualModel()
    metrics_collector.log_timing("initialization", "turn_detection", time.time() - td_start)
    
    total_init = time.time() - init_start
    metrics_collector.log_timing("initialization", "total", total_init)
    logger.info(f"✅ All components initialized in {total_init*1000:.2f}ms")
    
    # Create session
    session_start = time.time()
    session = AgentSession(
        stt=stt_instance,
        llm=llm_instance,
        tts=tts_instance,
        vad=vad_instance,
        turn_detection=turn_detector,
    )
    
    # Connect metrics collection
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        metrics_collector.collect_agent_metrics(ev)
    
    metrics_collector.log_timing("initialization", "session", time.time() - session_start)
    
    # Start session
    logger.info("🎬 Starting agent session...")
    start_time = time.time()
    await session.start(
        room=ctx.room,
        agent=MonitoredAssistant(metrics_collector),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    metrics_collector.log_timing("session", "start", time.time() - start_time)
    
    # Generate initial greeting
    logger.info("👋 Generating initial greeting...")
    greeting_start = time.time()
    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )
    metrics_collector.log_timing("session", "initial_greeting", time.time() - greeting_start)
    
    # Setup shutdown callback to log final summary
    async def log_final_summary():
        logger.info("=" * 80)
        logger.info("📊 FINAL METRICS SUMMARY")
        logger.info("=" * 80)
        
        summary = metrics_collector.get_summary()
        
        # Log usage summary
        logger.info("\n💰 Usage Summary:")
        logger.info(json.dumps(summary["usage"], indent=2))
        
        # Log statistics
        logger.info("\n📈 Performance Statistics:")
        for component, stats in summary["statistics"].items():
            logger.info(f"\n  {component}:")
            for key, value in stats.items():
                logger.info(f"    {key}: {value:.2f}" if isinstance(value, float) else f"    {key}: {value}")
        
        # Log all pipeline events
        logger.info(f"\n🔄 Pipeline Events ({len(summary['pipeline_events'])} total):")
        for event in summary["pipeline_events"][-10:]:  # Last 10 events
            logger.info(f"  {event}")
            
        logger.info("\n" + "=" * 80)
        
    ctx.add_shutdown_callback(log_final_summary)
    
    logger.info("✨ Agent is ready and listening!")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))