import asyncio
import json
import logging
from collections.abc import AsyncIterable
from pathlib import Path

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
from helpers.config import (
    LLM_PROVIDER,
    SESSION_ID,
    SESSION_LOGS,
    STT_PROVIDER,
    TTS_PROVIDER,
)
from helpers.customer_helper import load_customer_profile
from helpers.log_usage import log_usage
from helpers.metrics import setup_metrics
from instructions import get_instructions

load_dotenv(".env.local")
logger = logging.getLogger("agent")

class MyAssistant(Agent):
    def __init__(self, session : AgentSession, **kwargs):
        customer_profile=load_customer_profile()
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

    # async def on_exit(self):
    #     """Triggered when session is ending — ensure summary generation if user spoke."""
    #     logger.info("Session ending. Checking if summary should be generated...")

    #     if not self.call_started:
    #         logger.info("Call never started (user didn't pick up). Skipping summary.")
    #         return

    #     if self.summary_generated:
    #         logger.info("Summary already generated earlier. Skipping duplicate.")
    #         return

    #     try:
    #         history_text = extract_conversation(self.session_ref)
    #         customer_data = {
    #             "customer_profile": dict(self.customer_profile)
    #         }
    #         summary = await generate_summary_llm(history_text, customer_data)
    #         logger.info("Summary generated successfully at call end: %s", summary)
    #         self.summary_generated = True

    #         # Optionally hang up gracefully
    #         await hangup_current_room()
    #     except Exception as e:
    #         logger.exception(f"Error during on_exit summary generation: {e}")

    async def on_exit(self):
        """Triggered when session is ending — ensure summary and customer data are saved."""
        logger.info("Session ending. Ensuring summary and data storage...")

        try:
            if not self.call_started:
                logger.info("Call never started (user didn't pick up). Skipping summary.")
                return

            # ✅ Always extract conversation
            history_text = extract_conversation(self.session_ref)
            customer_data = {
                "customer_profile": dict(self.customer_profile)
            }

            # ✅ Generate summary if not already done
            summary = None
            if not self.summary_generated:
                summary = await generate_summary_llm(history_text, customer_data)
                logger.info("✅ Summary generated at call end.")
                self.summary_generated = True
            else:
                logger.info("Summary already generated earlier.")
                summary = "Already generated earlier."

            # ✅ Prepare file save path
            session_id = SESSION_ID
            participant_id = self.customer_profile.get("customer_id", "unknown_participant")

            base_dir = Path(__file__).resolve().parent.parent / "temp"
            base_dir.mkdir(parents=True, exist_ok=True)
            filepath = base_dir / f"{session_id}_{participant_id}.json"

            # ✅ Prepare data to save
            data = {
                "session_id": session_id,
                "participant_id": participant_id,
                "customer_profile": self.customer_profile,
                "summary": summary,
            }

            # ✅ Save JSON file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            logger.info(f"💾 Session data saved to {filepath}")
            usage_collector, cost_calc = setup_metrics(self.session, SESSION_LOGS)
            await log_usage(
                usage_collector=usage_collector,
                cost_calc=cost_calc,
                SESSION_LOGS=SESSION_LOGS,
                SESSION_ID=SESSION_ID,
                customer_profile=self.customer_profile,
                TTS_PROVIDER=TTS_PROVIDER,
                STT_PROVIDER=STT_PROVIDER,
                LLM_PROVIDER=LLM_PROVIDER
            )

            # ✅ Hang up gracefully
            await hangup_current_room()

        except Exception as e:
            logger.exception(f"❌ Error during on_exit summary/data save: {e}")


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
