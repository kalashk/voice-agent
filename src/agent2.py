import logging
from collections.abc import AsyncIterable
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from dotenv import load_dotenv
from langfuse import Langfuse

#from langfuse.client import StatefulClient
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    ChatContext,
    ChatMessage,
    FunctionTool,
    JobContext,
    ModelSettings,
    RoomInputOptions,
    RoomOutputOptions,
    UserStateChangedEvent,
    WorkerOptions,
    cli,
    llm,
    stt,
)
from livekit.agents.llm import ChatChunk
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins.turn_detector.english import EnglishModel

logger = logging.getLogger("openai-voice-agent")
logger.setLevel(logging.INFO)

load_dotenv()

_langfuse = Langfuse()

INSTRUCTIONS = """
You are a technical support AI for CloudDash, a SaaS analytics platform.

IMPORTANT: Respond in plain text only. Do not use any markdown formatting such as bold, italics, bullet points, or numbered lists. Your responses will be read aloud by text-to-speech.

Your goal is to help users troubleshoot CloudDash issues through conversation.

Guidelines:
- Keep answers short and easy to understand
- Ask clarifying questions only when needed
- Provide clear, step-by-step verbal instructions
- If visual assistance is requested, politely explain that you are a voice-only assistant
"""

class VoiceAgent(Agent):
    """A voice-only agent with STT, LLM, and TTS capabilities (no video)."""

    def __init__(self, instructions: str, room: rtc.Room) -> None:
        super().__init__(
            instructions=instructions,
            llm=openai.LLM(model="gpt-4.1"),
            stt=deepgram.STT(),
            tts=cartesia.TTS(
                model="sonic-2",
                speed="fast",
                voice="bf0a246a-8642-498a-9950-80c35e9276b5",
            ),
            vad=silero.VAD.load(),
            turn_detection=EnglishModel(),
        )
        self.room = room
        self.session_id = str(uuid4())
        self.current_trace = None

    async def close(self) -> None:
        """Clean up session and flush traces."""
        if self.current_trace:
            self.current_trace = None
        _langfuse.flush()

    async def on_enter(self) -> None:
        """Called when the agent joins the room."""
        self.session.generate_reply(instructions="introduce yourself very briefly")
        self.session.on("user_state_changed", self.on_user_state_change)
        logger.info("VoiceAgent entered session.")

    async def on_exit(self) -> None:
        """Called when the agent is about to leave."""
        await self.session.generate_reply(
            instructions="tell the user a friendly goodbye before you exit"
        )
        await self.close()
        logger.info("VoiceAgent exited session.")

    def get_current_trace(self):
        """Return or create a Langfuse trace for monitoring."""
        if self.current_trace:
            return self.current_trace
        self.current_trace = _langfuse.trace(  # type: ignore[attr-defined]
                name="voice_agent",
                session_id=self.session_id,
            )
        return self.current_trace

    # Monitor user state
    def on_user_state_change(self, event: UserStateChangedEvent) -> None:
        logger.info(f"User state changed: {event.old_state} -> {event.new_state}")

    async def on_user_turn_completed(
        self, turn_ctx: ChatContext, new_message: ChatMessage,
    ) -> None:
        """Called whenever the user finishes speaking."""
        self.current_trace = _langfuse.trace(  # type: ignore[attr-defined]
                name="voice_agent",
                session_id=self.session_id,
            )
        logger.info(f"User turn completed {self.get_current_trace().trace_id}")

    async def stt_node(
        self, audio: AsyncIterable[rtc.AudioFrame], model_settings: ModelSettings
    ) -> Optional[AsyncIterable[stt.SpeechEvent]]:
        """Convert speech to text using Deepgram."""
        span = self.get_current_trace().span(name="stt_node", metadata={"model": "deepgram"})
        try:
            async for event in Agent.default.stt_node(self, audio, model_settings):
                if event.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                    logger.info(f"Speech recognized: {event.alternatives[0].text[:80]}...")
                yield event
        except Exception as e:
            span.update(level="ERROR")
            logger.error(f"STT error: {e}")
            raise
        finally:
            span.end()

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[FunctionTool | llm.RawFunctionTool],
        model_settings: ModelSettings,
    ) -> AsyncIterable[llm.ChatChunk]:
        """Generate spoken responses using GPT."""
        copied_ctx = chat_ctx.copy()

        # messages = openai.utils.to_chat_ctx(copied_ctx, cache_key=self.llm)
        messages, _ = copied_ctx.to_provider_format("openai")
        generation = self.get_current_trace().generation(
            name="llm_generation",
            model="gpt-4.1",
            input=messages
        )

        output = ""
        started = False
        try:
            async for raw_chunk in Agent.default.llm_node(self, copied_ctx, tools, model_settings):
                    # Narrow the type dynamically
                    if isinstance(raw_chunk, str):
                        # Skip or handle textual intermediary chunks if needed
                        continue

                    chunk: ChatChunk = raw_chunk  # type: ignore
                    if not started:
                        generation.update(completion_start_time=datetime.now(timezone.utc))
                        started = True

                    if chunk.delta and chunk.delta.content:
                        output += chunk.delta.content
                    yield chunk
        except Exception as e:
            generation.update(level="ERROR")
            logger.error(f"LLM error: {e}")
            raise
        finally:
            generation.end(output=output)

    async def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        """Convert text to speech with Cartesia TTS."""
        span = self.get_current_trace().span(name="tts_node", metadata={"model": "cartesia"})
        try:
            async for frame in Agent.default.tts_node(self, text, model_settings):
                yield frame
        except Exception as e:
            span.update(level="ERROR")
            logger.error(f"TTS error: {e}")
            raise
        finally:
            span.end()


# ----------------------------------------
# Entrypoint
# ----------------------------------------

async def entrypoint(ctx: JobContext) -> None:
    """Main entry point for running the VoiceAgent."""
    await ctx.connect()

    logger.info(f"Connected to room: {ctx.room.name}")
    # logger.info(f"Local participant: {ctx.room.local_participant.identity}")

    # if len(ctx.room.remote_participants) == 0:
    #     logger.info("No remote participants in room, exiting")
    #     return

    session = AgentSession()
    agent = VoiceAgent(instructions=INSTRUCTIONS, room=ctx.room)

    room_input = RoomInputOptions(audio_enabled=True, video_enabled=False)
    room_output = RoomOutputOptions(audio_enabled=True, transcription_enabled=True)

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=room_input,
        room_output_options=room_output,
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
