# assistants/tts_utils.py
import logging
import re
from collections.abc import AsyncIterable

logger = logging.getLogger("tts_utils")

def get_pronunciations(tts_provider: str) -> dict:
    """Return a mapping of words → phonetic replacements based on provider."""
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

    if tts_provider == "cartesia":
        pronunciations.update({
            "Kajal": "काजल",
            "kaajal": "काजल",
        })

    return pronunciations


async def adjust_text_for_tts(
    input_text: AsyncIterable[str],
    pronunciations: dict
) -> AsyncIterable[str]:
    """
    Process text for TTS:
    - Removes <think> / reasoning markers (¤, ¶)
    - Applies pronunciation replacements
    - Yields cleaned text for speech synthesis
    """
    in_think = False
    buffer = ""
    think_buffer = ""

    async for chunk in input_text:
        buffer += chunk

        # Detect start of think section
        if "¤" in buffer:
            before, _, after = buffer.partition("¤")
            buffer = before
            in_think = True
            think_buffer = ""
            logger.debug("Think section started.")
            continue

        # Inside think
        if in_think:
            if "¶" in buffer:
                pre_think, _, after = buffer.partition("¶")
                think_buffer += pre_think
                token_count = len(think_buffer.strip())
                logger.debug("Think section ended. Tokens (chars): %d", token_count)
                buffer = after
                in_think = False
                think_buffer = ""
            else:
                think_buffer += buffer
                buffer = ""
                continue

        # Apply pronunciation replacements
        cleaned = buffer
        for term, replacement in pronunciations.items():
            cleaned = re.sub(
                rf"(?<!\w){re.escape(term)}(?!\w)",
                replacement,
                cleaned,
                flags=re.IGNORECASE
            )

        if cleaned.strip():
            yield cleaned

        buffer = ""
