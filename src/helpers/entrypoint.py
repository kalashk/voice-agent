import asyncio
import json
import logging

from dotenv import load_dotenv
from langfuse import get_client
from livekit.agents import (
    JobContext,
    RoomInputOptions,
)
from livekit.plugins import noise_cancellation

from class_mod.assistant import MyAssistant
from helpers.config import (
    LLM_PROVIDER,
    SESSION_ID,
    SESSION_LOGS,
    STT_PROVIDER,
    TTS_PROVIDER,
)

# Import customer functions
from helpers.customer_helper import load_customer_profile
from helpers.log_usage import log_usage
from helpers.metrics import setup_metrics
from helpers.setup_session import setup_session
from helpers.setup_tts_stt import setup_llm, setup_stt, setup_tts

tracker = get_client()

logger = logging.getLogger("agent")
load_dotenv(".env.local")  # Load environment variables

SESSION_ID = SESSION_ID

async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the assistant.
    - Loads customer profile via load_customer.py
    - Optionally updates name, gender, phone interactively based on user input
    - Sets up session, metrics, and starts assistant
    """
    try:
        logging.basicConfig(level=logging.DEBUG)

        logger.debug("SESSION ID IS (inside entry point) --------------------------",{SESSION_ID})
        # Load customer profile
        customer_profile = load_customer_profile()

        # Store profile metadata into the job for tracking
        ctx.job.metadata = json.dumps(customer_profile)
        metadata = json.loads(ctx.job.metadata)
        logger.info(f"User profile loaded: {metadata}")

        # Setup session with STT, TTS, LLM
        session = setup_session(
            ctx,
            setup_llm,
            setup_stt,
            setup_tts,
            LLM_PROVIDER,
            STT_PROVIDER,
            TTS_PROVIDER
        )

        # Setup usage metrics
        usage_collector, cost_calc = setup_metrics(session, SESSION_LOGS)

        # Shutdown callback to log usage
        ctx.add_shutdown_callback(
            lambda: log_usage(
                usage_collector=usage_collector,
                cost_calc=cost_calc,
                SESSION_LOGS=SESSION_LOGS,
                SESSION_ID=SESSION_ID,
                customer_profile=customer_profile,
                TTS_PROVIDER=TTS_PROVIDER,
                STT_PROVIDER=STT_PROVIDER,
                LLM_PROVIDER=LLM_PROVIDER
            )
        )

        # Create assistant
        assistant = MyAssistant(customer_profile, session=session)

        # Connect to LiveKit room
        await ctx.connect()

        # Start session with assistant and noise cancellation
        await session.start(
            agent=assistant,
            room=ctx.room,
            room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
        )

        await asyncio.sleep(3)

        # Generate initial greeting
        # reply = await session.generate_reply(
        #     instructions="simply greet with namaste and introduce yourself with your name and bank name, nothing else, keep it very simple and short, without think tag, dont think here",
        # )
        # print("LLM →", reply.chat_items)

        tracker.flush()

    except Exception as e:
        logger.exception("Error in entrypoint")
        raise e
