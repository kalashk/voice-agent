import re
import os
import json
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import AsyncIterable
from livekit import rtc, api
from livekit.agents import Agent, AgentSession
from livekit.agents.voice import ModelSettings
from livekit.agents import function_tool, RunContext, get_job_context
from instructions import get_instructions
from helpers.config import TTS_PROVIDER
from helpers.customer_helper import CustomerProfileType

# External LLM dependencies for independent summary generation
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv(".env.local")
logger = logging.getLogger("agent")

summary_instructions = """
        You are a call summary generator for a car loan sales assistant.
        Analyze the entire conversation and output a JSON object with these keys:
        - call_metadata
        - customer_profile
        - vehicle_information
        - financial_information
        - intent_and_qualification
        - summary_text
        
        Follow this JSON schema exactly:
        "customer_profile": {{
            "name": "string or null",
            "gender": "male | female | unknown",
            "age_estimate": "number or null",
            "location_city": "string or null",
            "occupation_type": "Salaried | Self-Employed | Business Owner | Unknown"
        }},
        "vehicle_information": {{
            "vehicle_type": "Car | SUV | Commercial | Unknown",
            "make_model": "string or null",
            "registration_year": "number or null",
            "ownership_status": "Owned | Financed | New Purchase | Not Mentioned",
            "current_loan_provider": "string or null"
        }},
        "financial_information": {{
            "monthly_income_bracket": "Below 25k | 25k-50k | 50k-1L | Above 1L | Unknown",
            "existing_emi_burden": "Low | Moderate | High | Unknown",
            "cibil_score_discussed": "Yes | No",
            "approximate_cibil_score": "number or null",
            "loan_amount_requested": "number or null",
            "tenure_requested_months": "number or null"
        }},
        "intent_and_qualification": {{
            "interested_in_loan": "Yes | No | Maybe",
            "reason_if_not_interested": "string or null",
            "shared_documents_on_whatsapp": "Yes | No | Pending",
            "documents_mentioned": ["PAN", "Aadhaar", "Salary Slip"],
            "communication_tone": "Cooperative | Polite | Rude | Disinterested",
            "follow_up_needed": "Yes | No",
            "preferred_follow_up_time": "string or null"
        }},
        "summary_text": "2-3 sentences natural summary."
        }}

        Output ONLY valid JSON.
        """

# ---------------- LLM for summary ----------------
summarizer_llm = ChatGroq(model="moonshotai/kimi-k2-instruct-0905", temperature=0.3)
parser = JsonOutputParser(pydantic_object={
    "type": "object"
})  # pydantic validation, will be enforced via LLM
prompt_template = ChatPromptTemplate.from_messages([
    ("system", summary_instructions),
    ("user", "{input}")
])
summary_chain = prompt_template | summarizer_llm | parser

async def generate_summary_llm(history_text: str) -> dict:
    """Call LLM independently to generate JSON summary from conversation history."""
    logger.info("Generating call summary via independent LLM...")
    logger.info("History Text: %s", history_text[:500])
    result = summary_chain.invoke({"input": history_text})
    try:
        summary_json = json.loads(json.dumps(result))  # ensure JSON serializable
    except Exception:
        summary_json = {"error": "Invalid JSON generated", "raw_text": str(result)}


    logger.info("Generated Summary: %s", summary_json)
    return summary_json

# ---------------- Conversation extraction ----------------
# def extract_conversation(session: AgentSession) -> str:
#     """Extract conversation history as a single text block."""
#     history_dict = session.history.to_dict()
#     logger.info("Extracting conversation history from session. : %s", history_dict)
#     messages = []
#     for msg in history_dict.get("messages", []):
#         role = msg.get("role", "unknown")
#         content = msg.get("content", "")
#         messages.append(f"{role}: {content}")
#     return "\n".join(messages)

# def extract_conversation(session: AgentSession) -> str:
#     """Extract conversation history as a clean, readable text block."""
#     history_dict = session.history.to_dict()
#     logger.info("Extracting conversation history from session. : %s", history_dict)

#     messages = []
#     for msg in history_dict.get("messages", []):
#         role = msg.get("role", "unknown")
#         content = msg.get("content", "")
#         # Flatten list contents
#         if isinstance(content, list):
#             content = " ".join([str(c) for c in content])
#         elif not isinstance(content, str):
#             content = str(content)
#         messages.append(f"{role}: {content.strip()}")
#     return "\n".join(messages)

def extract_conversation(session: AgentSession, *, max_messages: int = 5000, max_chars: int = 800000) -> str:
    """
    Extract conversation history as a clean, readable text block.

    - Handles history keys: 'items', 'messages', or 'entries'.
    - Flattens content lists/dicts into readable text.
    - Returns up to `max_messages` last messages and truncates to `max_chars`.
    """
    history_dict = session.history.to_dict()
    logger.info("Extracting conversation history from session. : %s", history_dict)

    # support various history shapes
    raw_items = history_dict.get("items") or history_dict.get("messages") or history_dict.get("entries") or []
    # take last N messages to avoid huge prompts
    raw_items = raw_items[-max_messages:]

    def _flatten_content(content) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for elem in content:
                if isinstance(elem, str):
                    parts.append(elem)
                elif isinstance(elem, dict):
                    # common shapes: {"text": "..."} or {"content": "..."}
                    text = elem.get("text") or elem.get("content") or elem.get("value") or None
                    if text and isinstance(text, str):
                        parts.append(text)
                    else:
                        # fallback to serializing small dicts
                        parts.append(" ".join(str(v) for v in elem.values() if isinstance(v, str)))
                else:
                    parts.append(str(elem))
            return " ".join([p for p in parts if p])
        if isinstance(content, dict):
            return content.get("text") or content.get("content") or " ".join(
                str(v) for v in content.values() if isinstance(v, str)
            )
        return str(content)

    messages = []
    for item in raw_items:
        # make sure we only process messages
        if item.get("type") and item["type"] != "message":
            continue

        role = item.get("role", "unknown")
        content = item.get("content", "")
        content_text = _flatten_content(content).strip()
        if not content_text:
            # sometimes 'transcript' or nested fields are present
            alt = item.get("transcript") or item.get("text") or item.get("message")
            content_text = _flatten_content(alt).strip()
        if not content_text:
            # skip empty messages
            continue

        # optional timestamp formatting
        ts = item.get("timestamp") or item.get("created_at") or item.get("time")
        if ts is not None:
            try:
                # if numeric epoch
                ts_float = float(ts)
                ts_str = datetime.fromtimestamp(ts_float).isoformat()
            except Exception:
                ts_str = str(ts)
            messages.append(f"{role} [{ts_str}]: {content_text}")
        else:
            messages.append(f"{role}: {content_text}")

    result = "\n".join(messages)

    # truncate to max_chars (keep tail which contains the latest content)
    if len(result) > max_chars:
        result = result[-max_chars:]
        # safe cutoff: start from next line break to avoid cutting mid-token
        first_newline = result.find("\n")
        if first_newline > 0:
            result = result[first_newline + 1 :]

    return result




# ---------------- Hangup function ----------------
async def hangup_current_room():
    """Gracefully close the LiveKit room for this job."""
    ctx = get_job_context()
    if ctx is None or ctx.room is None:
        logger.warning("No active room found. Cannot hang up.")
        return

    room_name = ctx.room.name
    print(f"🛑 Deleting room: {room_name}")
    logger.info(f"Deleting room: {room_name}")

    try:
        await ctx.api.room.delete_room(api.DeleteRoomRequest(room=room_name))
        print(f"✅ Room '{room_name}' deleted successfully.")
        logger.info(f"Room '{room_name}' deleted successfully.")
    except Exception as e:
        print(f"❌ Failed to delete room: {e}")
        logger.error(f"Failed to delete room: {e}")

class MyAssistant(Agent):
    def __init__(self, customer_profile: CustomerProfileType, session : AgentSession, **kwargs):
        instructions = get_instructions(customer_profile)
        super().__init__(instructions=instructions)
        self.customer_profile = customer_profile
        self.session_ref = session       

    async def tts_node(
        self,
        text: AsyncIterable[str],
        model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        """
        Custom TTS node:
        - Remove <think> tags from LLM output
        - Apply pronunciation replacements
        - Send to default TTS engine
        """

        # Define phonetic replacements
        pronunciations = {
            "umm": "अं-ं--..",
            "uhm": "अं-ं--..",
            "ahh": "आ-ं--आह..",
            "ah": "आ-ं--आह..",
            "HDFC": "एच-डी-एफ-सी",
            "hdfc": "एच-डी-एफ-सी",
            "EMI": "ई-एम-आई",
            "emi": "ई-एम-आई",
            "ROI": "आर-ओ-आई",
            "ITR": "आई-टी-आर",
            "PAN": "पैन",
            "Aadhar": "आधार",
            "Tenure": "टे-न्योर",
            "Interest": "इंट-रेस्ट",
            "Loan": "लोन",
            "Car": "कार",
            "Vehicle": "व्हीकल",
            "Finance": "फायनेंस",
            "Refinance": "री-फायनेंस",
            "Balance Transfer": "बैलेंस ट्रांसफर",
            "Top-Up": "टॉप-अप",
            "Salaried": "सैल-रिड",
            "Businessman": "बिज़-नेस-मैन",
            "Flat Rate": "फ्लैट रेट",
            "Reducing Rate": "रिड्यूसिंग रेट",
            "Personal Loan": "पर्सनल लोन",
            "Business Loan": "बिज़-नेस लोन",
        }

        if TTS_PROVIDER == "cartesia":
            pronunciations.update({
                "Kajal": "काजल",
                "kaajal": "काजल",
            })

        # Async generator to adjust text before TTS
        async def adjust_text(input_text: AsyncIterable[str]) -> AsyncIterable[str]:
            async for chunk in input_text:
                # Remove <think> tags
                cleaned = re.sub(r"<think>.*?</think>", " ", chunk, flags=re.DOTALL)
                # Apply phonetic replacements
                for term, replacement in pronunciations.items():
                    cleaned = re.sub(
                        rf"(?<!\w){re.escape(term)}(?!\w)",
                        replacement,
                        cleaned,
                        flags=re.IGNORECASE
                    )
                yield cleaned

        # Feed the processed text into default TTS
        async for frame in Agent.default.tts_node(self, adjust_text(text), model_settings):
            yield frame

    async def _end_call_with_summary(self, context: RunContext, goodbye_instructions: str) -> dict:
        # 1️⃣ Generate goodbye message
        logger.info("Generating goodbye message before ending the call.")
        handle = await context.session.generate_reply(instructions=goodbye_instructions)
        await handle.wait_for_playout()
        await asyncio.sleep(1)

        # 2️⃣ Generate summary using independent LLM
        logger.info("Extracting conversation history for summary generation.")
        history_text = extract_conversation(context.session)
        summary = await generate_summary_llm(history_text)

        # 3️⃣ Hangup room
        logger.info("Hanging up the current room.")
        await hangup_current_room()

        logger.info("Call ended and summary generated.")
        return summary
    

    # ---------------- End-call functions ----------------
    @function_tool(name="end_call", description="End the call.")
    async def end_positive_call(self, context: RunContext):
        logger.info("Ending call as customer is interested in the loan.")
        instructions = "Say you will call back to customer later and politely end the call."
        return await self._end_call_with_summary(context, instructions)