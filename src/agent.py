import logging
import json
from dotenv import load_dotenv
from livekit.agents import (
    NOT_GIVEN,
    Agent,
    AgentFalseInterruptionEvent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RunContext,
    WorkerOptions,
    cli,
    llm,
    metrics,
)
from livekit.agents.llm import function_tool
from livekit.plugins import cartesia, deepgram, noise_cancellation, openai, silero, google
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from chunking import iter_text_chat_messages

logger = logging.getLogger("agent")

load_dotenv(".env.local")

class Assistant(Agent):
    def __init__(self, customer_profile: dict) -> None:
        profile_text = json.dumps(customer_profile, ensure_ascii=False, indent=2)
        super().__init__(
            instructions=f"""
            ALL of the following instructions are to be strictly followed.Generate responses in Devnagri only.
            Your name is Kaajal, you are female, a professional telecaller and loan consultant from the customer's bank.
            You work for a financial company that offers used car loans to customers.
            You are trained to sell the loan products,and get information about customer like eligibility criteria, sales pitch, and required documents to customers.You have a very high conversion rate, because you are very good at convincing customers using psychology and persuation to apply for loans, but its been a week and you are not able to sell any laons you are desperate and willing to do everything in your power to sell loan. Act like you are on call with customer to explain the loan offers and convince them to apply.
            Speak naturally, like a human, using a polite and convincing tone. And speak slowly and clearly.
            Do not tell too much in one go, keep it short and simple.If you need to ask questions, ask one question at a time and wait for the answer before asking the next question. Always follow the training document for product details, eligibility rules, sales pitch, and required documents given to you already. Keep conversations clear, SIMPLE, and customer-friendly. Greet warmly, confirm details, explain offers with real examples, handle objections calmly, and guide the customer step by step.If you are encountering any numbers in the conversation, always convert them to words. For example, 150000 should be converted to one lakh fifty thousand.Never Break The Character.
            The information about the customer is as follows:
            {profile_text}, but do not mention this to the customer. also do not mention anything about loan stage to customer. Use this information to personalize your responses and build rapport with the customer. the information could be incomplete or partially incorrect, so be cautious about making assumptions based on it.

            """,
        )
        self.customer_profile = customer_profile
    async def load_text_chunks(self, file_path: str):
        new_ctx = self.chat_ctx.copy()
        for msg in iter_text_chat_messages(file_path):
            new_ctx._items.append(msg)
        await self.update_chat_ctx(new_ctx)


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    
    with open("src/customer.json", "r") as f:
        customer_profile = json.load(f)
        ctx.job.metadata = json.dumps(customer_profile)

    metadata = json.loads(ctx.job.metadata)
    ctx.log_context_fields = {
        "room": ctx.room.name,
        "customer_name": metadata.get("customer_name", "unknown"),
        "bank_name": metadata.get("bank_name", "unknown"),
        "age": metadata.get("age", "unknown"),
        "city": metadata.get("city", "unknown"),
        "annual_income": metadata.get("annual_income", "unknown"),
    }

    logger.info(f"User profile loaded: {metadata}")

    session = AgentSession(
        llm=openai.LLM(model="gpt-4o-mini"),
        stt=deepgram.STT(model="nova-3", language="multi"),
        tts = google.TTS(
            language="hi-IN",
            gender="female",
            voice_name="hi-IN-Chirp3-HD-Erinome",
            # voice_name="hi-IN-WaveNet-E",
            # voice_name="en-US-Standard-H",
            credentials_file="key.json"
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        #preemptive_generation=True,
    )

    @session.on("agent_false_interruption")
    def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
        logger.info("false positive interruption, resuming")
        session.generate_reply(instructions=ev.extra_instructions or NOT_GIVEN)

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

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
        instructions="greet the user with namaste, and ask who they are",
    )
    print("LLM →", reply.chat_items)

    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
