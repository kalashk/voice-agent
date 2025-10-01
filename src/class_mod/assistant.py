import re
from copy import deepcopy
from livekit import rtc
from typing import AsyncIterable
from livekit.agents import Agent, AgentSession
from livekit.agents.voice import ModelSettings
from instructions import get_instructions
from helpers.config import TTS_PROVIDER
from livekit.agents.llm import LLM

class MyAssistant(Agent):
    def __init__(self, customer_profile: dict, session : AgentSession, **kwargs):
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
            "EMI": "ई-एम-आई",
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

    async def query_llm_silently(self, llm: LLM, prompt: str) -> str:
        # Create a temporary context to avoid touching main session memory
        temp_ctx = deepcopy(self.chat_ctx)
        temp_ctx.add_message(role = "developer", content=prompt)

        async with llm.chat(chat_ctx=temp_ctx) as stream:  # returns LLMStream
            text = ""
            async for chunk in stream.to_str_iterable():
                text += chunk
        return text


