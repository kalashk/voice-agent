from config import TTS_PROVIDER, STT_PROVIDER 
from livekit.plugins import cartesia, deepgram, noise_cancellation, openai, silero, google, resemble, sarvam

# --------------------------
#   TTS (Text-to-Speech) Setup
# --------------------------
def setup_tts(provider: str = TTS_PROVIDER):
    """
    Initialize a TTS engine based on the selected provider.
    Returns an instance of the TTS plugin ready to generate audio.
    """

    if provider == "openai":
        # OpenAI TTS (gpt-4o-mini-tts) with a friendly, conversational voice
        return openai.TTS(
            model="gpt-4o-mini-tts", 
            voice="nova", 
            instructions="Speak friendly and conversationally."
        )
    elif provider == "cartesia":
        # Cartesia TTS using Sonic-2 model, voice ID, and Hindi language
        return cartesia.TTS(
            model="sonic-2", 
            voice="9cebb910-d4b7-4a4a-85a4-12c79137724c", 
            # hummm voice
            # voice="56e35e2d-6eb6-4226-ab8b-9776515a7094",
            language="hi",
        )
    elif provider == "cartesia_filler":
        # Cartesia TTS using Sonic-2 model, voice ID, and Hindi language
        return cartesia.TTS(
            model="sonic-2", 
            voice="56e35e2d-6eb6-4226-ab8b-9776515a7094",
            language="en",
        )
    elif provider == "google_chirp":
        # Google Cloud TTS using Chirp voices for Hindi
        return google.TTS(
            language="hi-IN",
            gender="female",
            voice_name="hi-IN-Chirp3-HD-Erinome",
            credentials_file="key.json",
            # Another voice option: "hi-IN-Chirp3-HD-Sulfat"
        )
    elif provider == "sarvam_anushka":
        # Sarvam TTS with Hindi target language, speaker 'anushka'
        return sarvam.TTS(
            target_language_code="hi-IN",
            speaker="anushka",
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
    elif provider == "cartesia":
        # Cartesia STT using 'ink-whisper' model, specifically for Hindi
        return cartesia.STT(
            model="ink-whisper", 
            language="hi"
        )
    else:
        # Raise error if provider is unknown
        raise ValueError(f"Unknown STT provider: {provider}")
