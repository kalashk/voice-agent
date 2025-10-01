import os
import logging
import json
from dotenv import load_dotenv
from livekit.agents import (
    JobContext,
    RoomInputOptions,
)
from livekit.plugins import noise_cancellation
from helpers.setup_tts_stt import setup_tts, setup_stt, setup_llm
from helpers.metrics import setup_metrics
from helpers.log_usage import log_usage
from helpers.helpers import load_customer_profile, setup_session
from class_mod.assistant import MyAssistant
from helpers.config import SESSION_ID,SESSION_LOGS,TTS_PROVIDER,STT_PROVIDER,LLM_PROVIDER

logger = logging.getLogger("agent")   # Logger for debugging and info logs
load_dotenv(".env.local")             # Load environment variables from .env.local file

async def entrypoint(ctx: JobContext):
    """
    The main entrypoint for running the assistant.
    Handles setup, session management, metrics, and conversation flow.
    """
    try:
        logging.basicConfig(level=logging.DEBUG)   # Setup logging
        print("Starting agent...")

        # Attach room info to logs for better traceability
        # room_name = ctx.room.name
        # ctx.log_context_fields = {"room": ctx.room.name}
        print(ctx.room.name)
        room_name = os.getenv("ROOM_NAME")
        ctx.log_context_fields = {"room": room_name}

        # Load customer profile (e.g., preferences, name, history)
        customer_profile = load_customer_profile()

        # Store profile metadata into the job for tracking
        ctx.job.metadata = json.dumps(customer_profile)
        metadata = json.loads(ctx.job.metadata)
        logger.info(f"User profile loaded: {metadata}")

        # Setup session with STT (speech-to-text), TTS (text-to-speech)
        session = setup_session(
            ctx,
            setup_llm, 
            setup_stt, 
            setup_tts, 
            LLM_PROVIDER, 
            STT_PROVIDER, 
            TTS_PROVIDER
        )

        # Setup usage metrics (collect cost, tokens, events, etc.)
        usage_collector, cost_calc = setup_metrics(session, SESSION_LOGS)

        # Add a shutdown callback to log usage metrics at the end
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

        # Create Assistant instance with user profile
        assistant = MyAssistant(customer_profile, session=session)

        # Connect to the LiveKit room
        await ctx.connect()

        # Start session with assistant and noise cancellation enabled
        await session.start(
            agent=assistant,
            room=ctx.room,
            room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
        )

        # Generate an initial greeting reply (short introduction)
        reply = await session.generate_reply(
            instructions="simply greet with namaste and introduce yourself, keep it simple and short, without think tag, dont think here",
        )
        print("LLM →", reply.chat_items)   # Print AI response to console


    except Exception as e:
        # Log any errors and re-raise
        logger.exception("Error in entrypoint")
        raise e