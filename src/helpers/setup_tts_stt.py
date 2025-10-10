# from helpers.config import TTS_PROVIDER, STT_PROVIDER, LLM_PROVIDER
from livekit.plugins import cartesia, deepgram, sarvam, openai, google, groq, lmnt
from helpers.config import TTS_PROVIDER, STT_PROVIDER,LLM_PROVIDER

# --------------------------
#   TTS (Text-to-Speech) Setup
# --------------------------
def setup_tts(provider: str = TTS_PROVIDER):
    """
    Initialize a TTS engine based on the selected provider.
    Returns an instance of the TTS plugin ready to generate audio.
    """
    if provider == "cartesia":
        # Cartesia TTS using Sonic-2 model, voice ID, and Hindi language
        return cartesia.TTS(
            model="sonic-2-2025-03-07", 
            #voice="9cebb910-d4b7-4a4a-85a4-12c79137724c", 
            voice='faf0731e-dfb9-4cfc-8119-259a79b27e12',
            language="hi",
            text_pacing=True,
            word_timestamps=True,
            speed=-0.2,
            emotion=['positivity:high', 'sadness'],
        )
    elif provider == "lmnt":
        return lmnt.TTS(
            voice="bella",
            temperature=0.7
        )
    elif provider == "sarvam_anushka":
        # Sarvam TTS with Hindi target language, speaker 'anushka'
        return sarvam.TTS(
            target_language_code="hi-IN",
            speaker="anushka",
            pace=0.95,
            #enable_preprocessing=True,
        )
    elif provider == "sarvam_manisha":
        # Sarvam TTS with Hindi target language, speaker 'manisha'
        return sarvam.TTS(
            target_language_code="hi-IN",
            speaker="manisha",
            pace=0.95,
            #enable_preprocessing=True,
        )
    else:
        # Raise error if provider is unknown
        raise ValueError(f"Unknown TTS provider: {provider}")
    

# --------------------------
#   STT (Speech-to-Text) Setup
# --------------------------
def setup_stt(provider: str = STT_PROVIDER):
    """
    Initialize an STT engine based on the selected provider.
    Returns an instance of the STT plugin ready to transcribe audio.
    """

    if provider == "deepgram":
        # Deepgram STT using 'nova-3' model and multi-language support
        return deepgram.STT(
            model="nova-3", 
            language="multi"
        )
    elif provider == "sarvam":
        return sarvam.STT(
            language="hi-IN",
            model="saarika:v2.5"
        )
    else:
        # Raise error if provider is unknown
        raise ValueError(f"Unknown STT provider: {provider}")

def setup_llm(provider: str = LLM_PROVIDER):
    if provider == "openai":
        return openai.LLM(model="gpt-5-mini-2025-08-07")
    elif provider == "groq openai gpt-oss-120b":
        return groq.LLM(
            model="openai/gpt-oss-120b", 
            tool_choice='none'
            )
    elif provider == "groq meta-llama llama-4-scout-17b-16e-instruct":
        return groq.LLM(
            model="meta-llama/llama-4-scout-17b-16e-instruct", 
            tool_choice='auto',
            temperature=0.1
            )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")