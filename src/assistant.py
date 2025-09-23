# from typing import Any
# from livekit import rtc
# from livekit.agents import Agent, AgentSession
# import re
# from livekit import rtc
# from livekit.agents.voice import ModelSettings
# from typing import AsyncIterable
# from instructions import get_instructions
# from config import TTS_PROVIDER
# from livekit.agents import llm, NOT_GIVEN

# # --------------------------
# #   Assistant Definition
# # --------------------------
# class MyAssistant(Agent):
#     """
#     Custom Assistant that extends the base LiveKit Agent.
#     - Uses the main pipeline TTS for normal LLM responses
#     - Uses a secondary "filler_tts" provider for quick acknowledgements like "ok sir"
#     - Can also be extended to play "thinking sounds" while waiting for LLM
#     """
#     def __init__(self, customer_profile: dict, session: AgentSession, **kwargs) -> None:
#         instructions = get_instructions(customer_profile)
#         super().__init__(instructions=instructions)

#         self.customer_profile = customer_profile
#         self.session_ref = session          # session reference for say()/output

#     async def llm_node(self, chat_ctx, tools, model_settings=None):
#         print("LLM NODE HIT PING PONG BLING BONG")

#         activity = self._get_activity_or_raise()

#         if activity.llm is None or isinstance(activity.llm, type(NOT_GIVEN)):
#             raise RuntimeError("llm_node called but no LLM is available")

#         if isinstance(activity.llm, llm.RealtimeModel):
#             # Realtime models don’t expose `.chat`, they use session-based APIs
#             raise RuntimeError(
#                 "llm_node cannot be used with a RealtimeModel. Use realtime_llm_session instead."
#             )

#         assert isinstance(activity.llm, llm.LLM), "Expected llm to be an LLM instance"
#         tool_choice = model_settings.tool_choice if model_settings else NOT_GIVEN
#         conn_options = activity.session.conn_options.llm_conn_options

#         async with activity.llm.chat(
#             chat_ctx=chat_ctx,
#             tools=tools,
#             tool_choice=tool_choice,
#             conn_options=conn_options,
#         ) as stream:
#             async for chunk in stream:
#                 if chunk is None:
#                     continue

#                 content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
#                 if content is None:
#                     yield chunk
#                     continue

#                 processed_content = content.replace("<think>", " ").replace("</think>", " ")
#                 if hasattr(chunk, "delta") and getattr(chunk.delta, "content", None):
#                     if chunk.delta and chunk.delta.content:
#                         if processed_content:
#                             chunk.delta.content = processed_content
#                             yield chunk
#                 else:
#                     yield chunk
       
#     # To improve pronunciation of filler words like "umm", "uhm", "ahh", we can preprocess the text before passing it to the TTS engine. Here, we replace these filler words with phonetic representations that the TTS engine can pronounce more clearly.    
#     async def tts_node(
#         self,
#         text: AsyncIterable[str],
#         model_settings: ModelSettings
#     ) -> AsyncIterable[rtc.AudioFrame]:
#         # Pronunciation replacements for common technical terms and abbreviations.
#         # We are adding filler words here and replacing them with Devanagari script.
#         if TTS_PROVIDER != "cartesia": 
#             pronunciations = {
#                 "umm": "अं-ं--..", # Adding a hyphen between the nasal sounds
#                 "uhm": "अं-ं--..", 
#                 "ahh": "आ-ं--आह..",
#                 "ah": "आ-ं--आह..",
#                 "HDFC" : "एच-डी-एफ-सी",
#                 "hdfc" : "एच-डी-एफ-सी",
#                 "EMI" : "ई-एम-आई",
#                 "emi" : "ई-एम-आई",
#                 "ROI" : "आर-ओ-आई",
#                 "ITR" : "आई-टी-आर",
#                 "PAN" : "पैन",
#                 "pan" : "पैन",
#                 "Aadhar" : "आधार",
#                 "Tenure" : "टे-न्योर",
#                 "Interest" : "इंट-रेस्ट",
#                 "Loan" : "लोन",
#                 "Car" : "कार",
#                 "Vehicle" : "व्हीकल",
#                 "Finance" : "फायनेंस",
#                 "Refinance" : "री-फायनेंस",
#                 "Balance Transfer" : "बैलेंस ट्रांसफर",
#                 "Top-Up" : "टॉप-अप",
#                 "Salaried" : "सैल-रिड",
#                 "Businessman" : "बिज़-नेस-मैन",
#                 "Flat Rate" : "फ्लैट रेट",
#                 "Reducing Rate" : "रिड्यूसिंग रेट",
#                 "Personal Loan" : "पर्सनल लोन",
#                 "Business Loan" : "बिज़-नेस लोन",
#             }
#             if TTS_PROVIDER == 'cartesia':
#                 pronunciations.update({
#                     "Kajal": "काजल",
#                     "kaajal": "काजल",
#                 })

#         async def adjust_pronunciation(input_text: AsyncIterable[str]) -> AsyncIterable[str]:
#             async for chunk in input_text:
#                 modified_chunk = chunk
#                 for term, pronunciation in pronunciations.items():
#                     # Unicode-safe replacement using lookahead/lookbehind
#                     modified_chunk = re.sub(
#                         rf'(?<!\w){re.escape(term)}(?!\w)',
#                         pronunciation,
#                         modified_chunk,
#                         flags=re.IGNORECASE
#                     )
#                 yield modified_chunk

#         # Process with modified text through base TTS implementation
#         async for frame in Agent.default.tts_node(
#             self,
#             adjust_pronunciation(text),
#             model_settings
#         ):
#             yield frame


from typing import AsyncIterable
import re
from livekit import rtc
from livekit.agents import Agent
from livekit.agents.voice import ModelSettings
from instructions import get_instructions
from config import TTS_PROVIDER

class MyAssistant(Agent):
    def __init__(self, customer_profile: dict, session, **kwargs):
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

    # async def transcription_node(
    #         self, 
    #         text: AsyncIterable[str], 
    #         model_settings: ModelSettings
    #     ) -> AsyncIterable[str]:
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
    #         "EMI": "ई-एम-आई",
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

    #     async for chunk in text:
    #         # remove <think> tags
    #         cleaned = re.sub(r"<think>.*?</think>", " ", chunk, flags=re.DOTALL)
    #         # apply phonetic replacements
    #         for term, replacement in pronunciations.items():
    #             cleaned = re.sub(rf"(?<!\w){re.escape(term)}(?!\w)", replacement, cleaned, flags=re.IGNORECASE)
    #         # collapse multiple spaces
    #         cleaned = re.sub(r"\s+", " ", cleaned).strip()
    #         yield cleaned

