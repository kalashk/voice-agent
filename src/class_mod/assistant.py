import re
import asyncio
from livekit import rtc, api
from typing import AsyncIterable
from livekit.agents import Agent, AgentSession
from livekit.agents.voice import ModelSettings
from instructions import get_instructions
from helpers.config import TTS_PROVIDER
from livekit.agents.llm import LLM
from helpers.customer_helper import CustomerProfileType
from livekit.agents import function_tool, RunContext, get_job_context

async def hangup_current_room():
    """Gracefully close the LiveKit room for this job."""
    ctx = get_job_context()
    if ctx is None or ctx.room is None:
        print("⚠️ No active room found. Cannot hang up.")
        return

    room_name = ctx.room.name
    print(f"🛑 Deleting room: {room_name}")

    try:
        await ctx.api.room.delete_room(api.DeleteRoomRequest(room=room_name))
        print(f"✅ Room '{room_name}' deleted successfully.")
    except Exception as e:
        print(f"❌ Failed to delete room: {e}")

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

    @function_tool(name="hangup", description="To end the call")
    async def end_session(self, context: RunContext):
        """Politely end the LiveKit call for everyone."""
        # Step 1: Say goodbye
        await context.session.say("Sayonara Senpai! It was great talking to you. Have a wonderful day!")
        # Step 2: Small pause before hangup
        await asyncio.sleep(5)

        # Step 3: Delete the room (ends SIP + agent)
        await hangup_current_room()

        return "Session ended gracefully."