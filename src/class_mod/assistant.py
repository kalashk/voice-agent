import asyncio

#import json
import logging

#import re
from collections.abc import AsyncIterable

#from datetime import datetime
from dotenv import load_dotenv
from langfuse import observe

# from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.prompts import ChatPromptTemplate
# External LLM dependencies for independent summary generation
# from langchain_groq import ChatGroq
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    FunctionTool,
    RunContext,
    function_tool,
    llm,
    #    get_job_context,
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

# summary_instructions = """
#         You are a call summary generator for a car loan sales assistant.
#         Analyze the entire conversation and output a JSON object with these keys:
#         - call_metadata
#         - customer_profile
#         - vehicle_information
#         - financial_information
#         - intent_and_qualification
#         - summary_text

#         Follow this JSON schema exactly:
#         "customer_profile": {{
#             "name": "string or null",
#             "gender": "male | female | unknown",
#             "age_estimate": "number or null",
#             "location_city": "string or null",
#             "occupation_type": "Salaried | Self-Employed | Business Owner | Unknown"
#         }},
#         "vehicle_information": {{
#             "vehicle_type": "Car | SUV | Commercial | Unknown",
#             "make_model": "string or null",
#             "registration_year": "number or null",
#             "ownership_status": "Owned | Financed | New Purchase | Not Mentioned",
#             "current_loan_provider": "string or null"
#         }},
#         "financial_information": {{
#             "monthly_income_bracket": "Below 25k | 25k-50k | 50k-1L | Above 1L | Unknown",
#             "existing_emi_burden": "Low | Moderate | High | Unknown",
#             "cibil_score_discussed": "Yes | No",
#             "approximate_cibil_score": "number or null",
#             "loan_amount_requested": "number or null",
#             "tenure_requested_months": "number or null"
#         }},
#         "intent_and_qualification": {{
#             "interested_in_loan": "Yes | No | Maybe",
#             "reason_if_not_interested": "string or null",
#             "shared_documents_on_whatsapp": "Yes | No | Pending",
#             "documents_mentioned": ["PAN", "Aadhaar", "Salary Slip"],
#             "communication_tone": "Cooperative | Polite | Rude | Disinterested",
#             "follow_up_needed": "Yes | No",
#             "preferred_follow_up_time": "string or null"
#         }},
#         "summary_text": "2-3 sentences natural summary."
#         }}

#         Output ONLY valid JSON.
#         """

# # ---------------- LLM for summary ----------------
# summarizer_llm = ChatGroq(model="moonshotai/kimi-k2-instruct-0905", temperature=0.3)
# parser = JsonOutputParser(pydantic_object={
#     "type": "object"
# })  # pydantic validation, will be enforced via LLM
# prompt_template = ChatPromptTemplate.from_messages([
#     ("system", summary_instructions),
#     ("user", "{input}")
# ])
# summary_chain = prompt_template | summarizer_llm | parser

# async def generate_summary_llm(history_text: str, customer_data: dict) -> dict:
#     """Call LLM independently to generate JSON summary from conversation history + customer metadata."""
#     logger.info("Generating call summary via independent LLM...")

#     # Prepare contextualized input for the LLM
#     llm_input = f"""
#     CUSTOMER CONTEXT:
#     The following is structured customer information collected before or during the call.
#     {json.dumps(customer_data, indent=2, ensure_ascii=False)}

#     CONVERSATION HISTORY:
#     {history_text}
#     """

#     result = summary_chain.invoke({"input": llm_input})
#     try:
#         summary_json = json.loads(json.dumps(result))  # ensure JSON serializable
#     except Exception as e:
#         logger.error("Failed to parse summary JSON: %s", e)
#         summary_json = {"error": "Invalid JSON generated", "raw_text": str(result)}

#     logger.info("Generated Summary: %s", summary_json)
#     return summary_json

# ---------------- Conversation extraction ----------------
# def extract_conversation(session: AgentSession, *, max_messages: int = 5000, max_chars: int = 800000) -> str:
#     """
#     Extract conversation history as a clean, readable text block.

#     - Handles history keys: 'items', 'messages', or 'entries'.
#     - Flattens content lists/dicts into readable text.
#     - Returns up to `max_messages` last messages and truncates to `max_chars`.
#     """
#     history_dict = session.history.to_dict()
#     logger.info("Extracting conversation history from session. : %s", history_dict)

#     # support various history shapes
#     raw_items = history_dict.get("items") or history_dict.get("messages") or history_dict.get("entries") or []
#     # take last N messages to avoid huge prompts
#     raw_items = raw_items[-max_messages:]

#     def _flatten_content(content) -> str:
#         if content is None:
#             return ""
#         if isinstance(content, str):
#             return content
#         if isinstance(content, list):
#             parts = []
#             for elem in content:
#                 if isinstance(elem, str):
#                     parts.append(elem)
#                 elif isinstance(elem, dict):
#                     # common shapes: {"text": "..."} or {"content": "..."}
#                     text = elem.get("text") or elem.get("content") or elem.get("value") or None
#                     if text and isinstance(text, str):
#                         parts.append(text)
#                     else:
#                         # fallback to serializing small dicts
#                         parts.append(" ".join(str(v) for v in elem.values() if isinstance(v, str)))
#                 else:
#                     parts.append(str(elem))
#             return " ".join([p for p in parts if p])
#         if isinstance(content, dict):
#             return content.get("text") or content.get("content") or " ".join(
#                 str(v) for v in content.values() if isinstance(v, str)
#             )
#         return str(content)

#     messages = []
#     for item in raw_items:
#         # make sure we only process messages
#         if item.get("type") and item["type"] != "message":
#             continue

#         role = item.get("role", "unknown")
#         content = item.get("content", "")
#         content_text = _flatten_content(content).strip()
#         if not content_text:
#             # sometimes 'transcript' or nested fields are present
#             alt = item.get("transcript") or item.get("text") or item.get("message")
#             content_text = _flatten_content(alt).strip()
#         if not content_text:
#             # skip empty messages
#             continue

#         # optional timestamp formatting
#         ts = item.get("timestamp") or item.get("created_at") or item.get("time")
#         if ts is not None:
#             try:
#                 # if numeric epoch
#                 ts_float = float(ts)
#                 ts_str = datetime.fromtimestamp(ts_float).isoformat()
#             except Exception:
#                 ts_str = str(ts)
#             messages.append(f"{role} [{ts_str}]: {content_text}")
#         else:
#             messages.append(f"{role}: {content_text}")

#     result = "\n".join(messages)

#     # truncate to max_chars (keep tail which contains the latest content)
#     if len(result) > max_chars:
#         result = result[-max_chars:]
#         # safe cutoff: start from next line break to avoid cutting mid-token
#         first_newline = result.find("\n")
#         if first_newline > 0:
#             result = result[first_newline + 1 :]

#     return result


# ---------------- Hangup function ----------------
# async def hangup_current_room():
#     """Gracefully close the LiveKit room for this job."""
#     ctx = get_job_context()
#     if ctx is None or ctx.room is None:
#         logger.warning("No active room found. Cannot hang up.")
#         return

#     room_name = ctx.room.name
#     print(f"🛑 Deleting room: {room_name}")
#     logger.info(f"Deleting room: {room_name}")

#     try:
#         await ctx.api.room.delete_room(api.DeleteRoomRequest(room=room_name))
#         print(f"✅ Room '{room_name}' deleted successfully.")
#         logger.info(f"Room '{room_name}' deleted successfully.")
#     except Exception as e:
#         print(f"❌ Failed to delete room: {e}")
#         logger.error(f"Failed to delete room: {e}")

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
            instructions="Greet the customer with 'Namaste' and briefly introduce yourself with your name and bank name. Keep it very short and polite."
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

    # async def tts_node(
    #     self,
    #     text: AsyncIterable[str],
    #     model_settings: ModelSettings
    # ) -> AsyncIterable[rtc.AudioFrame]:
    #     """
    #     Custom TTS node:
    #     - Remove <think> tags from LLM output
    #     - Apply pronunciation replacements
    #     - Send to default TTS engine
    #     """

    #     # Define phonetic replacements
    #     pronunciations = {
    #         "umm": "अं-ं--..",
    #         "uhm": "अं-ं--..",
    #         "ahh": "आ-ं--आह..",
    #         "ah": "आ-ं--आह..",
    #         "HDFC": "एच-डी-एफ-सी",
    #         "hdfc": "एच-डी-एफ-सी",
    #         "EMI": "ई-एम-आई",
    #         "emi": "ई-एम-आई",
    #         "ROI": "आर-ओ-आई",
    #         "ITR": "आई-टी-आर",
    #         "PAN": "पैन",
    #         "Aadhar": "आधार",
    #         "Tenure": "टे-न्योर",
    #         "Interest": "इंट-रेस्ट",
    #         "Loan": "लोन",
    #         "Car": "कार",
    #         "Vehicle": "व्हीकल",
    #         "Finance": "फायनेंस",
    #         "Refinance": "री-फायनेंस",
    #         "Balance Transfer": "बैलेंस ट्रांसफर",
    #         "Top-Up": "टॉप-अप",
    #         "Salaried": "सैल-रिड",
    #         "Businessman": "बिज़-नेस-मैन",
    #         "Flat Rate": "फ्लैट रेट",
    #         "Reducing Rate": "रिड्यूसिंग रेट",
    #         "Personal Loan": "पर्सनल लोन",
    #         "Business Loan": "बिज़-नेस लोन",
    #     }

    #     if TTS_PROVIDER == "cartesia":
    #         pronunciations.update({
    #             "Kajal": "काजल",
    #             "kaajal": "काजल",
    #         })

    #     async def adjust_text(input_text: AsyncIterable[str]) -> AsyncIterable[str]:
    #         in_think = False
    #         buffer = ""
    #         think_buffer = ""  # stores reasoning text for counting

    #         async for chunk in input_text:
    #             # logger.debug("Original chunk: %s", chunk)
    #             buffer += chunk

    #             # Check for start marker (¤)
    #             if "¤" in buffer:
    #                 before, _, after = buffer.partition("¤")
    #                 buffer = before
    #                 in_think = True
    #                 think_buffer = ""  # reset reasoning buffer
    #                 logger.debug("Think section started.")
    #                 print("¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤")
    #                 # continue collecting upcoming tokens into think_buffer
    #                 continue

    #             # If we are currently in a reasoning section, accumulate
    #             if in_think:
    #                 # Check if reasoning ends in this same chunk
    #                 if "¶" in buffer:
    #                     pre_think, _, after = buffer.partition("¶")
    #                     think_buffer += pre_think
    #                     token_count = len(think_buffer.strip())
    #                     logger.debug(
    #                         "Think section ended. Tokens (chars): %d, text: %s",
    #                         token_count,
    #                         think_buffer.strip()[:120] + ("..." if len(think_buffer) > 120 else "")
    #                     )
    #                     print("¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤")
    #                     buffer = after
    #                     in_think = False
    #                     think_buffer = ""
    #                 else:
    #                     # still inside think, accumulate and skip emitting
    #                     think_buffer += buffer
    #                     buffer = ""
    #                     continue

    #             # Process the visible (speakable) part
    #             cleaned = buffer
    #             for term, replacement in pronunciations.items():
    #                 cleaned = re.sub(
    #                     rf"(?<!\w){re.escape(term)}(?!\w)",
    #                     replacement,
    #                     cleaned,
    #                     flags=re.IGNORECASE
    #                 )

    #             if cleaned.strip():
    #                 yield cleaned
    #                 # logger.debug("Yielded cleaned text: %s", cleaned.strip())

    #             # reset buffer for next chunk
    #             buffer = ""

    #     # Feed the processed text into default TTS
    #     async for frame in Agent.default.tts_node(self, adjust_text(text), model_settings):
    #         yield frame

    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        pronunciations = get_pronunciations(TTS_PROVIDER)
        async for frame in Agent.default.tts_node(self, adjust_text_for_tts(text, pronunciations), model_settings):
            yield frame


    # async def _end_call_with_summary(self, context: RunContext, goodbye_instructions: str) -> dict:
    #     """Ends the call gracefully and generates LLM-based summary including customer metadata."""
    #     logger.info("Generating goodbye message before ending the call.")

    #     logger.info("Extracting conversation history for summary generation.")
    #     history_text = extract_conversation(context.session)

    #     # --- Include customer data ---
    #     customer_data = {
    #         "customer_profile": self.customer_profile
    #         if hasattr(self.customer_profile, "dict")
    #         else dict(self.customer_profile)
    #     }

    #     # --- Generate summary with context ---
    #     summary = await generate_summary_llm(history_text, customer_data)

    #     # --- Hang up gracefully ---
    #     logger.info("Hanging up the current room in 7 sec.")
    #     await asyncio.sleep(7)
    #     await hangup_current_room()

    #     logger.info("Call ended and summary generated.")
    #     return summary

    # ---------------- End-call functions ----------------
    # @function_tool(name="end_call", description="End the call.")
    # async def end_positive_call(self, context: RunContext):
    #     logger.info("Ending call as customer is interested in the loan.")
    #     instructions = "Say goodbye, very briefly"
    #     return await self._end_call_with_summary(context, instructions)

    async def _end_call(self, context: RunContext, goodbye_instructions: str) -> None:
        """Ends the call gracefully (without generating summary)."""
        logger.info("Generating goodbye message before ending the call.")
        await context.session.generate_reply(instructions=goodbye_instructions)

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
