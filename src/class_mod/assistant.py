import asyncio
import logging
from collections.abc import AsyncIterable

from dotenv import load_dotenv
from langfuse import observe
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    FunctionTool,
    RunContext,
    function_tool,
    llm,
    stt,
)
from livekit.agents.llm import ChatChunk
from livekit.agents.voice import ModelSettings

from class_mod.assistant_helpers import extract_conversation, hangup_current_room
from class_mod.summary import generate_summary_llm
from class_mod.tts_utils import adjust_text_for_tts, get_pronunciations
from helpers.config import TTS_PROVIDER
from helpers.customer_helper import CustomerProfileType
from instructions import get_instructions

load_dotenv(".env.local")
logger = logging.getLogger("agent")

class MyAssistant(Agent):
    def __init__(self, customer_profile: CustomerProfileType, session : AgentSession, **kwargs):
        instructions = get_instructions(customer_profile)
        super().__init__(instructions=instructions)
        self.customer_profile = customer_profile
        self.session_ref = session
        self.call_started = False
        self.summary_generated = False

    async def on_enter(self):
        """Called when the agent first joins the LiveKit room."""
        logger.info("Agent joined the session, sending greeting...")
        await self.session_ref.generate_reply(
            instructions="Greet the customer with 'Namaste' and briefly introduce yourself with your name and bank name. Keep it very short and polite"
        )
        self.call_started = True
        logger.info("Greeting sent successfully.")

    async def on_exit(self):
        """Triggered when session is ending — ensure summary generation if user spoke."""
        logger.info("Session ending. Checking if summary should be generated...")

        if not self.call_started:
            logger.info("Call never started (user didn't pick up). Skipping summary.")
            return

        if self.summary_generated:
            logger.info("Summary already generated earlier. Skipping duplicate.")
            return

        try:
            history_text = extract_conversation(self.session_ref)
            customer_data = {
                "customer_profile": dict(self.customer_profile)
            }
            summary = await generate_summary_llm(history_text, customer_data)
            logger.info("Summary generated successfully at call end: %s", summary)
            self.summary_generated = True

            # Optionally hang up gracefully
            await hangup_current_room()
        except Exception as e:
            logger.exception(f"Error during on_exit summary generation: {e}")

    @observe(name="stt_node")
    async def stt_node(
        self, audio: AsyncIterable[rtc.AudioFrame], model_settings: ModelSettings
    ) -> AsyncIterable[stt.SpeechEvent]:
        """Convert speech to text using Deepgram."""
        try:
            async for event in Agent.default.stt_node(self, audio, model_settings):
                if event.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                    logger.info(f"STT result: {event.alternatives[0].text[:80]}...")
                yield event
        except Exception as e:
            logger.error(f"STT error: {e}")
            raise

    @observe(name="llm_node")
    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[FunctionTool | llm.RawFunctionTool],
        model_settings: ModelSettings,
    ) -> AsyncIterable[llm.ChatChunk]:
        """Generate responses using the LLaMA Scout 17B model."""
        # Make a copy of chat context to avoid mutation
        copied_ctx = chat_ctx.copy()
        try:
            async for chunk in Agent.default.llm_node(self, copied_ctx, tools, model_settings):
                # Ensure only ChatChunk instances are yielded
                if isinstance(chunk, ChatChunk):
                    # Optional: log for tracker
                    # if chunk.delta and chunk.delta.content:
                    #     logger.info(f"LLM generated chunk: {chunk.delta.content[:80]}...")
                    yield chunk
                else:
                    # Ignore non-ChatChunk types (some backends may send "done" events or metadata)
                    continue
        except Exception as e:
            logger.exception(f"LLM node error: {e}")
            raise

    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        pronunciations = get_pronunciations(TTS_PROVIDER)
        async for frame in Agent.default.tts_node(self, adjust_text_for_tts(text, pronunciations), model_settings):
            yield frame

    async def _end_call(self, context: RunContext, goodbye_instructions: str) -> None:
        """Ends the call gracefully (without generating summary)."""
        #logger.info("Generating goodbye message before ending the call.")
        #await context.session.generate_reply(instructions=goodbye_instructions)

        # Graceful hangup after delay
        logger.info("Hanging up the current room in 5 sec.")
        await asyncio.sleep(5)
        await hangup_current_room()

        logger.info("Call ended by LLM-triggered function.")

    # ---------------- End-call function ----------------
    @function_tool(name="end_call", description="Politely end the call with the customer.")
    async def end_positive_call(self, context: RunContext):
        logger.info("Ending call as per LLM decision (user interested or conversation complete).")
        instructions = "Say goodbye politely and thank the customer for their time."
        await self._end_call(context, instructions)
        return {"status": "Call ended by LLM instruction."}
