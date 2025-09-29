from helpers.config import TTS_PROVIDER, STT_PROVIDER 
from livekit.plugins import cartesia, deepgram, sarvam

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
    elif provider == "sarvam_anushka":
        # Sarvam TTS with Hindi target language, speaker 'anushka'
        return sarvam.TTS(
            target_language_code="hi-IN",
            speaker="anushka",
            #enable_preprocessing=True,
        )
    elif provider == "sarvam_manisha":
        # Sarvam TTS with Hindi target language, speaker 'manisha'
        return sarvam.TTS(
            target_language_code="hi-IN",
            speaker="manisha",
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
