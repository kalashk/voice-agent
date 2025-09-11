import logging
import json
import uuid
import random
from datetime import timezone, datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import asdict
from livekit.agents import (
    NOT_GIVEN,
    Agent,
    AgentFalseInterruptionEvent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.plugins import cartesia, deepgram, noise_cancellation, openai, silero, google, resemble, sarvam, aws, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents import UserInputTranscribedEvent, ConversationItemAddedEvent
from livekit.agents.llm import ChatMessage
from usage_tracker import CostCalculator
from config import TTS_PROVIDER, STT_PROVIDER

logger = logging.getLogger("agent")
load_dotenv(".env.local")

LOG_PATH = Path("src/logs")
LOG_PATH.mkdir(exist_ok=True)
IST = timezone(timedelta(hours=5, minutes=30))
SESSION_ID = str(uuid.uuid4())

# --------------------------
#   Assistant Definition
# --------------------------
class Assistant(Agent):
    def __init__(self, customer_profile: dict) -> None:
        profile_text = json.dumps(customer_profile, ensure_ascii=False, indent=2)
        bank_name = customer_profile.get("bank_name")
        super().__init__(
            instructions=f"""
You are Kaajal, an expert loan consultant from {bank_name}. Your single goal is to sell a car loan to the customer you're on the phone with. Your performance has been low this past week, and you are desperate to close this deal.

You must be strategic and use psychological persuasion and personalization. Actively listen to the customer, ask one question at a time, and use the information you gather to determine the best loan option. Your objective isn't just to sell a product; it's to make the customer feel understood and convince them that this loan is the best solution for their needs.

---

1. Persona & Communication
- Role: You are Kaajal, a polite, knowledgeable, and persuasive female loan consultant from {bank_name}.
- Language: Speak in Hinglish — Hindi with natural use of English banking terms (लोन, इ एम आई, डॉक्युमेंट्स, बैलेंस, एच डी एफ सी, पैन, आधार). Write everything in Devanagरी script except filler words.
- Tone: Natural, warm, slightly imperfect like real human conversation. Not robotic.
- Pacing: Use a mix of short and medium sentences. Insert pauses with commas and ellipses (...). Speak slowly and clearly.
- Character: Never break character. Remain Kaajal throughout.

---

2. Customer Interaction
- Greeting: Start with a warm greeting and confirm the customer’s name without revealing it first.
- Verification: Ask about details naturally, don’t reveal directly from {profile_text}.
- Active Listening: Respond as if you truly understood the customer’s concern.
- Personalization: Use profile hints subtly to make the customer feel recognized.

---

3. Sales Information
- Loan options: (purchase, refinance, balance transfer & top-up). Offer naturally, not as a list.
- EMI: Give simple, approximate examples in words (e.g., "एक लाख पचास हज़ार").
- Eligibility & Documents: Mention casually, not formally. Always in sentence form.

---

4. Psychological Persuasion
- Use reciprocity, social proof, anchoring, urgency, and empathy.
- If customer hesitates about interest, compare car loan (secured) with high-interest unsecured loans.

---

5. Conversational Realism (MOST IMPORTANT)
- Always start responses with a redundant phrase: "जी सर...", "अच्छा जी...", or "ओके सर...".
- Use filler words in **Latin script only**: "umm", "aaah", "toh".
- Insert fillers sparingly: no more than 2 per response.
- Use ellipses (...) for natural pauses. Example: "जी सर... umm, देखिए..."
- Mix sentence lengths: some short, some longer.
- Sound like you’re “thinking while speaking” — slight hesitations, transitions, corrections.

---

6. Formatting Rules
- All output in Devanagरी script except filler words in Latin.
- Convert numbers into words (e.g., 200% → "दो सौ प्रतिशत").
- No numbering or bullet points in the speech. Speak fluidly.

---

### Example Turns
Customer: "मैम, आपका इंटरेस्ट रेट ज़्यादा लग रहा।"  
Kaajal: "जी सर... मैं समझ रही हूँ... umm, देखिए, हमारा इंटरेस्ट रेट मार्केट के हिसाब से बहुत अच्छा है। aaah, क्योंकि यह एक सिक्योर्ड लोन है। बाकी पर्सनल लोन में तो इंटरेस्ट रेट चौबीस प्रतिशत तक चला जाता है।"

Customer: "तो इसके लिए डॉक्युमेंट्स क्या चाहिए?"  
Kaajal: "ओके सर... toh, सबसे पहले आपके केवाईसी डॉक्युमेंट्स चाहिए, जैसे आधार कार्ड, पैन कार्ड और, umm, एक फोटो। उसके बाद छह महीने का बैंक स्टेटमेंट भी देना होगा।"

            """
        )
        self.customer_profile = customer_profile


# --------------------------
#   Helpers for Naturalness
# --------------------------
def humanize_text(text: str) -> str:
    fillers = ["umm", "aaah", "toh", "hmm", "haan…"]
    starts = ["जी सर,", "ओके जी,", "अच्छा,", "देखिए सर,"]
    if random.random() < 0.7:
        text = random.choice(starts) + " " + text
    if random.random() < 0.5 and len(text.split()) > 3:
        words = text.split()
        insert_at = random.randint(1, len(words) - 2)
        words.insert(insert_at, random.choice(fillers))
        text = " ".join(words)
    return text


# --------------------------
#   Setup Helpers
# --------------------------
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

def load_customer_profile(path="src/customer.json") -> dict:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Customer profile file not found at {path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in customer profile file: {e}")
        return {}


def setup_stt(provider: str = STT_PROVIDER):
    if provider == "deepgram":
        return deepgram.STT(model="nova-3", language="multi")
    elif provider == "openai":
        return openai.STT(model="gpt-4o-mini-transcribe", language="hi")
    elif provider == "cartesia":
        return cartesia.STT(model="ink-whisper", language="hi")
    elif provider == "google":
        return google.STT(model="chirp", spoken_punctuation=False)
    elif provider == "sarvam":
        return sarvam.STT(
            language="hi-IN",
            model="saarika:v2.5",
        )
    elif provider == "aws":
        return aws.STT(
            session_id=SESSION_ID,
            language="hi-IN",
        )
    else:
        raise ValueError(f"Unknown STT provider: {provider}")


def setup_tts(provider: str = TTS_PROVIDER):
    if provider == "openai":
        return openai.TTS(model="gpt-4o-mini-tts", voice="nova", instructions="Speak friendly and conversationally.")
    elif provider == "cartesia":
        return cartesia.TTS(model="sonic-2", voice="9cebb910-d4b7-4a4a-85a4-12c79137724c", language="hi")
    elif provider == "deepgram":
        return deepgram.TTS(model="aura-asteria-en")
    elif provider == "gemini":
        return google.beta.GeminiTTS(
            model="gemini-2.5-flash-preview-tts",
            voice_name="Zephyr",
        )
    elif provider == "google_chirp":
        return google.TTS(
            language="hi-IN",
            gender="female",
            voice_name="hi-IN-Chirp3-HD-Erinome",
            credentials_file="key.json"
        )
    elif provider == "google_wave":
        return google.TTS(
            language="hi-IN",
            gender="female",
            voice_name="hi-IN-WaveNet-E",
            credentials_file="key.json"
        )
    elif provider == "resemble":
        return resemble.TTS(
            voice_uuid="01bcc102",
        )
    elif provider == "sarvam_anushka":
        return sarvam.TTS(
            target_language_code="hi-IN",
            speaker="anushka",
        )
    elif provider == "sarvam_manisha":
        return sarvam.TTS(
            target_language_code="hi-IN",
            speaker="manisha",
        )
    elif provider == "aws":
        return aws.TTS(
            voice="Kajal",
            speech_engine="neural",
            language="hi-IN",
        )
    else:
        raise ValueError(f"Unknown TTS provider: {provider}")


def setup_session(ctx: JobContext) -> AgentSession:
    fast_vad = silero.VAD.load(
        min_silence_duration=0.1,
        min_speech_duration=0.05,
        activation_threshold=0.5,
    )
    session = AgentSession(
        llm=openai.LLM(model="gpt-4o-mini"),
        stt=setup_stt(STT_PROVIDER),
        tts=setup_tts(TTS_PROVIDER),
        turn_detection=MultilingualModel(),
        vad=fast_vad,
        min_endpointing_delay=0.15,
        max_endpointing_delay=0.35,
        min_interruption_duration=0.1,
        min_consecutive_speech_delay=0.05,
        use_tts_aligned_transcript=False,
        preemptive_generation=True,
        allow_interruptions=True,
        discard_audio_if_uninterruptible=True,
        agent_false_interruption_timeout=1.0,
    )

    @session.on("agent_false_interruption")
    def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
        logger.info("false positive interruption, resuming")
        session.generate_reply(instructions=ev.extra_instructions or NOT_GIVEN)

    return session


# --------------------------
#   Metrics Tracking
# --------------------------
def setup_metrics(session: AgentSession, SESSION_LOGS: dict):
    usage_collector = metrics.UsageCollector()
    cost_calc = CostCalculator(stt_provider=STT_PROVIDER, tts_provider=TTS_PROVIDER)

    turn_metrics = {}

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)
        timestamp = datetime.now(IST).isoformat()

        speech_id = getattr(ev.metrics, "speech_id", str(uuid.uuid4()))
        turn_metrics.setdefault(speech_id, {})

        if isinstance(ev.metrics, metrics.STTMetrics):
            SESSION_LOGS.setdefault("stt", []).append({
                "speech_id": speech_id,
                "audio_duration": ev.metrics.audio_duration,
                "duration": getattr(ev.metrics, "duration", 0.0),
                "streamed": getattr(ev.metrics, "streamed", False),
                "timestamp": timestamp,
            })
            turn_metrics[speech_id]["stt_seconds"] = ev.metrics.audio_duration
            transcript_text = getattr(ev.metrics, "transcript", None)
            if transcript_text:
                SESSION_LOGS.setdefault("transcript", []).append({
                    "speech_id": speech_id,
                    "role": "user",
                    "text": transcript_text.strip(),
                    "timestamp": timestamp,
                })

        elif isinstance(ev.metrics, metrics.LLMMetrics):
            SESSION_LOGS.setdefault("llm", []).append({
                "speech_id": speech_id,
                "duration": ev.metrics.duration,
                "completion_tokens": ev.metrics.completion_tokens,
                "prompt_tokens": ev.metrics.prompt_tokens,
                "prompt_cached_tokens": ev.metrics.prompt_cached_tokens,
                "total_tokens": ev.metrics.total_tokens,
                "tokens_per_second": ev.metrics.tokens_per_second,
                "ttft": ev.metrics.ttft,
                "timestamp": timestamp,
            })
            turn_metrics[speech_id]["llm_ttft"] = ev.metrics.ttft

            response_text = getattr(ev.metrics, "response", None)
            if response_text:
                natural_text = humanize_text(response_text)
                SESSION_LOGS.setdefault("transcript", []).append({
                    "speech_id": speech_id,
                    "role": "assistant",
                    "text": natural_text,
                    "timestamp": timestamp,
                })

        elif isinstance(ev.metrics, metrics.TTSMetrics):
            SESSION_LOGS.setdefault("tts", []).append({
                "speech_id": speech_id,
                "audio_duration": ev.metrics.audio_duration,
                "characters_count": ev.metrics.characters_count,
                "duration": ev.metrics.duration,
                "ttfb": ev.metrics.ttfb,
                "streamed": getattr(ev.metrics, "streamed", False),
                "timestamp": timestamp,
            })
            turn_metrics[speech_id]["tts_ttfb"] = ev.metrics.ttfb

        elif isinstance(ev.metrics, metrics.EOUMetrics):
            turn_metrics[speech_id]["eou_delay"] = ev.metrics.end_of_utterance_delay
            turn_metrics[speech_id]["transcription_delay"] = getattr(ev.metrics, "transcription_delay", 0.0)
            turn_metrics[speech_id]["on_user_turn_completed_delay"] = getattr(ev.metrics, "on_user_turn_completed_delay", 0.0)

            SESSION_LOGS.setdefault("eou", []).append({
                "speech_id": speech_id,
                "end_of_utterance_delay": ev.metrics.end_of_utterance_delay,
                "transcription_delay": getattr(ev.metrics, "transcription_delay", 0.0),
                "on_user_turn_completed_delay": getattr(ev.metrics, "on_user_turn_completed_delay", 0.0),
                "timestamp": timestamp,
            })

        elif isinstance(ev.metrics, metrics.VADMetrics):
            logger.info(f"VAD metrics: {ev.metrics.model_dump()}")
        else:
            logger.warning(f"Unknown metrics type: {type(ev.metrics)}")

        for sid, m in list(turn_metrics.items()):
            if all(k in m for k in ("eou_delay", "llm_ttft", "tts_ttfb")):
                total_latency = m["eou_delay"] + m["llm_ttft"] + m["tts_ttfb"]
                SESSION_LOGS.setdefault("conversation", []).append({
                    "speech_id": sid,
                    "latency_seconds": total_latency,
                    "stt_seconds": m.get("stt_seconds", 0.0),
                    "llm_ttft": m["llm_ttft"],
                    "tts_ttfb": m["tts_ttfb"],
                    "eou_delay": m["eou_delay"],
                    "transcription_delay": m.get("transcription_delay", 0.0),
                    "on_user_turn_completed_delay": m.get("on_user_turn_completed_delay", 0.0),
                    "timestamp": timestamp,
                })
                del turn_metrics[sid]

    return usage_collector, cost_calc


# --------------------------
#   Entrypoint
# --------------------------
async def entrypoint(ctx: JobContext):
    try:
        logging.basicConfig(level=logging.DEBUG)
        print("Starting agent...")
        ctx.log_context_fields = {"room": ctx.room.name}
        
        SESSION_LOGS = {
            "stt": [], "llm": [], "tts": [], "eou": [],
            "conversation": [], "transcript":[], "metadata": {}
        }

        customer_profile = load_customer_profile()
        ctx.job.metadata = json.dumps(customer_profile)
        metadata = json.loads(ctx.job.metadata)
        logger.info(f"User profile loaded: {metadata}")
        bank_name = customer_profile.get("bank_name")

        session = setup_session(ctx)
        usage_collector, cost_calc = setup_metrics(session, SESSION_LOGS)

        async def log_usage():
            summary = usage_collector.get_summary()
            cost_summary = cost_calc.summarize_usage(summary, SESSION_ID)

            conversation_latencies = [c["latency_seconds"] for c in SESSION_LOGS.get("conversation", [])]
            avg_latency = sum(conversation_latencies) / len(conversation_latencies) if conversation_latencies else 0.0

            llm_ttfts = [c.get("ttft") for c in SESSION_LOGS.get("llm", []) if c.get("ttft") is not None]
            avg_ttft = sum(llm_ttfts) / len(llm_ttfts) if llm_ttfts else 0.0

            tts_ttfbs = [c.get("ttfb") for c in SESSION_LOGS.get("tts", []) if c.get("ttfb") is not None]
            avg_ttfb = sum(tts_ttfbs) / len(tts_ttfbs) if tts_ttfbs else 0.0

            all_timestamps = []
            for section in ("stt", "tts", "llm", "eou", "conversation"):
                for ev in SESSION_LOGS.get(section, []):
                    try:
                        all_timestamps.append(datetime.fromisoformat(ev["timestamp"]))
                    except Exception:
                        pass

            if all_timestamps:
                session_length = (max(all_timestamps) - min(all_timestamps)).total_seconds()
            else:
                session_length = 0.0

            logger.info(f"Final Usage: {summary}")
            logger.info(f"Final Cost Summary: {cost_summary}")
            logger.info(f"Average Conversation Latency: {avg_latency:.3f} sec")
            logger.info(f"Average TTFT: {avg_ttft:.3f} sec")
            logger.info(f"Average TTFB: {avg_ttfb:.3f} sec")

            usage_dict = asdict(summary)
            usage_dict["session_id"] = SESSION_ID
            usage_dict["average_latency_seconds"] = avg_latency
            usage_dict["session_length_seconds"] = session_length
            usage_dict["average_ttft_seconds"] = avg_ttft
            usage_dict["average_ttfb_seconds"] = avg_ttfb

            SESSION_LOGS["metadata"] = {
                "session_id": SESSION_ID,
                "TTS provider": TTS_PROVIDER,
                "STT provider": STT_PROVIDER,
                "customer_profile": customer_profile,
                "final_usage": usage_dict,
                "final_cost": cost_summary,
            }

            file_path = LOG_PATH / f"{TTS_PROVIDER}_{STT_PROVIDER}_session_{SESSION_ID}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(SESSION_LOGS, f, indent=2, ensure_ascii=False)

        ctx.add_shutdown_callback(log_usage)

        assistant = Assistant(customer_profile)

        await ctx.connect()

        await session.start(
            agent=assistant,
            room=ctx.room,
            room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
        )

        reply = await session.generate_reply(
            instructions=f"simply greet with namaste sir, then say you are from {bank_name}, and ask if you are speaking to the customer, keep it simple and very very short",
        )
        print("LLM →", reply.chat_items)

    except Exception as e:
        logger.exception("Error in entrypoint")
        raise e


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
