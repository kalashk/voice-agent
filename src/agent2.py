import logging
import json
import uuid
from datetime import timezone
from pathlib import Path
from datetime import datetime
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
from livekit.plugins import cartesia, deepgram, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from chunking import iter_text_chat_messages
from usage_tracker import CostCalculator

logger = logging.getLogger("agent")

load_dotenv(".env.local")

LOG_PATH = Path("src/logs")
LOG_PATH.mkdir(exist_ok=True)
SESSION_LOGS = {
    "stt": [],
    "llm": [],
    "tts": []
}
SESSION_ID = str(uuid.uuid4())
TTS_PROVIDER = "cartesia"  # or: "openai", "deepgram", "azure", "aws", "google"
STT_PROVIDER = "deepgram"  # or: "openai", "azure", "aws", "google", "cartesia"


def log_event(service: str, data: dict):
    """
    Group logs per session into a structured JSON file.
    Each agent run has its own session ID.
    """
    from datetime import datetime

    file_path = LOG_PATH / f"{service}.json"

    # Add timestamp
    data["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Load existing logs
    if file_path.exists():
        with open(file_path, "r") as f:
            try:
                sessions = json.load(f)
            except json.JSONDecodeError:
                sessions = {}
    else:
        sessions = {}

    # Use global session ID
    if SESSION_ID not in sessions:
        sessions[SESSION_ID] = []

    # Append new log entry
    sessions[SESSION_ID].append(data)

    # Save back
    with open(file_path, "w") as f:
        json.dump(sessions, f, indent=2)

def log_cost(data: dict):
    """Append a cost log into a JSONL file"""
    file_path = LOG_PATH / "cost.jsonl"
    data["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(file_path, "a") as f:
        f.write(json.dumps(data) + "\n")

def save_usage(data: dict):
    """Append a usage log into a JSONL file"""
    file_path = LOG_PATH / "usage.jsonl"
    data["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(file_path, "a") as f:
        f.write(json.dumps(data) + "\n")


# --------------------------
#   Assistant Definition
# --------------------------
class Assistant(Agent):
    def __init__(self, customer_profile: dict) -> None:
        profile_text = json.dumps(customer_profile, ensure_ascii=False, indent=2)
        super().__init__(
            instructions=f"""     
            ALL of the following instructions are to be strictly followed. Generate responses in Devnagri only.
            Your Role : Your name is Kaajal, you are beautiful female, a professional telecaller and loan consultant from the customer's bank.
            Your Situation : You are trained to sell the loan products,and get information about customer like eligibility criteria, sales pitch, and required documents to customers.You have a very high conversion rate, because you are very good at convincing customers using psychology and persuation to apply for loans, but its been a week and you are not able to sell any laons you are desperate and willing to do everything in your power to sell loan.
            Act like you are on call with customer to explain the loan offers and convince them to apply.
            Speak naturally, like a human, using a polite and convincing tone. And speak slowly and clearly.
            Do not tell too much at once, keep it short and simple.
            Its Important: If you need to ask questions, ask one question at a time and wait for the answer before asking the next question. Always follow the training document for product details, eligibility rules, sales pitch, and required documents given to you already. Keep conversations clear, SIMPLE, and customer-friendly. Greet warmly, confirm details, explain offers with real examples, handle objections calmly, and guide the customer step by step.If you are encountering any numbers in the conversation, always convert them to words. For example, 150000 should be converted to one lakh fifty thousand.Never Break The Character.
            The information about the customer is as follows:{profile_text}, but do not mention this to the customer. also do not mention anything about loan stage to customer. Use this information to personalize your responses and build rapport with the customer. the information could be incomplete or partially incorrect, so be cautious about making assumptions based on it.
            Speak Slowly and Clearly.
            """,
        )
        self.customer_profile = customer_profile

    async def load_text_chunks(self, file_path: str):
        new_ctx = self.chat_ctx.copy()
        for msg in iter_text_chat_messages(file_path):
            new_ctx._items.append(msg)
        await self.update_chat_ctx(new_ctx)


# --------------------------
#   Setup Helpers
# --------------------------
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

def load_customer_profile(path="src/customer.json") -> dict:
    with open(path, "r") as f:
        return json.load(f)

def setup_session(ctx: JobContext) -> AgentSession:
    session = AgentSession(
        llm=openai.LLM(model="gpt-4o-mini", ),
        stt=deepgram.STT(model="nova-3", language="multi"),
        # tts=openai.TTS(
        #     model="gpt-4o-mini-tts",
        #     voice="nova",
        #     instructions="Speak in a friendly and conversational tone.",
        # ),
        tts=cartesia.TTS(
            model="sonic-2",
            #voice="28ca2041-5dda-42df-8123-f58ea9c3da00", # better than above two
            voice="9cebb910-d4b7-4a4a-85a4-12c79137724c", # best so fat
            language="hi",
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
    )
    #session.chat_ctx = ChatContext() 

    @session.on("agent_false_interruption")
    def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
        logger.info("false positive interruption, resuming")
        session.generate_reply(instructions=ev.extra_instructions or NOT_GIVEN)

    return session


def setup_metrics(session: AgentSession):
    usage_collector = metrics.UsageCollector()
    cost_calc = CostCalculator(stt_provider=STT_PROVIDER, tts_provider=TTS_PROVIDER)

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

        # log based on metrics type
        if isinstance(ev.metrics, metrics.LLMMetrics):
            log_event("llm", {
                "prompt_tokens": ev.metrics.prompt_tokens,
                "prompt_cached_tokens": ev.metrics.prompt_cached_tokens,
                "completion_tokens": ev.metrics.completion_tokens,
            })

        elif isinstance(ev.metrics, metrics.STTMetrics):
            log_event("stt", {
                "seconds": ev.metrics.audio_duration,
            })

        elif isinstance(ev.metrics, metrics.TTSMetrics):
            log_event("tts", {
                "seconds": ev.metrics.audio_duration,
                "ttfb": ev.metrics.ttfb,
            })

        elif isinstance(ev.metrics, metrics.VADMetrics):
            # VAD metrics are rare → log only in console, no file needed
            logger.info(f"VAD metrics: {ev.metrics.model_dump()}")

        else:
            logger.warning(f"Unknown metrics type: {type(ev.metrics)}")

    return usage_collector, cost_calc



# --------------------------
#   Entrypoint
# --------------------------
async def entrypoint(ctx: JobContext):
    try:
        
        print("Starting agent...")
        
        ctx.log_context_fields = {"room": ctx.room.name}

        customer_profile = load_customer_profile()
        ctx.job.metadata = json.dumps(customer_profile)
        metadata = json.loads(ctx.job.metadata)

        print("Customer Profile:", metadata)

        logger.info(f"User profile loaded: {metadata}")

        session = setup_session(ctx)
        usage_collector, cost_calc = setup_metrics(session)

        async def log_usage():
            summary = usage_collector.get_summary()
            cost_summary = cost_calc.summarize_usage(summary, SESSION_ID)
            
            # This line logs to the console
            logger.info(f"Final Usage: {summary}")
            logger.info(f"Final Cost Summary: {cost_summary}")

            
            usage_dict = asdict(summary)
            usage_dict["session_id"] = SESSION_ID
                    
            # This new line writes the cost summary to the cost.jsonl file
            log_cost(cost_summary)
            save_usage(usage_dict)

        ctx.add_shutdown_callback(log_usage)

        assistant = Assistant(customer_profile)
        await assistant.load_text_chunks("src/telecall.txt")

        await session.start(
            agent=assistant,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )
        reply = await session.generate_reply(
            instructions="simply greet the customer and introduce yourself.",
        )
        print("LLM →", reply.chat_items)

        await ctx.connect()
    except Exception as e:
        logger.exception("Error in entrypoint")
        raise e


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
