# import os
# import logging
# import asyncio
# import json
# from dotenv import load_dotenv
# from livekit.agents import (
#     JobContext,
#     RoomInputOptions,
# )
# from livekit.plugins import noise_cancellation
# from helpers.setup_tts_stt import setup_tts, setup_stt, setup_llm
# from helpers.metrics import setup_metrics
# from helpers.log_usage import log_usage
# from helpers.helpers import load_customer_profile, setup_session
# from class_mod.assistant import MyAssistant
# from helpers.config import SESSION_ID,SESSION_LOGS,TTS_PROVIDER,STT_PROVIDER,LLM_PROVIDER

# logger = logging.getLogger("agent")   # Logger for debugging and info logs
# load_dotenv(".env.local")             # Load environment variables from .env.local file

# async def entrypoint(ctx: JobContext):
#     """
#     The main entrypoint for running the assistant.
#     Handles setup, session management, metrics, and conversation flow.
#     """
#     try:
#         logging.basicConfig(level=logging.DEBUG)   # Setup logging
#         print("Starting agent...")

#         # Attach room info to logs for better traceability
#         # room_name = ctx.room.name
#         # ctx.log_context_fields = {"room": ctx.room.name}
#         print(ctx.room.name)
#         room_name = os.getenv("ROOM_NAME")
#         ctx.log_context_fields = {"room": room_name}

#         # Load customer profile (e.g., preferences, name, history)
#         customer_profile = load_customer_profile()

#         # Store profile metadata into the job for tracking
#         ctx.job.metadata = json.dumps(customer_profile)
#         metadata = json.loads(ctx.job.metadata)
#         logger.info(f"User profile loaded: {metadata}")

#         # Setup session with STT (speech-to-text), TTS (text-to-speech)
#         session = setup_session(
#             ctx,
#             setup_llm, 
#             setup_stt, 
#             setup_tts, 
#             LLM_PROVIDER, 
#             STT_PROVIDER, 
#             TTS_PROVIDER
#         )

#         # Setup usage metrics (collect cost, tokens, events, etc.)
#         usage_collector, cost_calc = setup_metrics(session, SESSION_LOGS)

#         # Add a shutdown callback to log usage metrics at the end
#         ctx.add_shutdown_callback(
#             lambda: log_usage(
#                 usage_collector=usage_collector,
#                 cost_calc=cost_calc,
#                 SESSION_LOGS=SESSION_LOGS,
#                 SESSION_ID=SESSION_ID,
#                 customer_profile=customer_profile,
#                 TTS_PROVIDER=TTS_PROVIDER,
#                 STT_PROVIDER=STT_PROVIDER,
#                 LLM_PROVIDER=LLM_PROVIDER
#             )
#         )

#         # Create Assistant instance with user profile
#         assistant = MyAssistant(customer_profile, session=session)

#         # Connect to the LiveKit room
#         await ctx.connect()

#         # Start session with assistant and noise cancellation enabled
#         await session.start(
#             agent=assistant,
#             room=ctx.room,
#             room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
#         )
#         await asyncio.sleep(3)
#         # Generate an initial greeting reply (short introduction)
#         reply = await session.generate_reply(
#             instructions="simply greet with namaste and introduce yourself, keep it very simple and short, without think tag, dont think here",
#         )
#         print("LLM →", reply.chat_items)   # Print AI response to console


#     except Exception as e:
#         # Log any errors and re-raise
#         logger.exception("Error in entrypoint")
#         raise e

import os
import logging
import asyncio
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
from helpers.helpers import setup_session
from class_mod.assistant import MyAssistant
from helpers.config import SESSION_ID, SESSION_LOGS, TTS_PROVIDER, STT_PROVIDER, LLM_PROVIDER

# Import customer functions
from helpers.customer_helper import load_customer_profile, update_customer_profile

logger = logging.getLogger("agent")
load_dotenv(".env.local")  # Load environment variables

async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the assistant.
    - Loads customer profile via load_customer.py
    - Optionally updates name, gender, phone interactively based on user input
    - Sets up session, metrics, and starts assistant
    """
    try:
        logging.basicConfig(level=logging.DEBUG)
        print("Starting agent...")

        # Room info
        room_name = os.getenv("ROOM_NAME", ctx.room.name)
        ctx.log_context_fields = {"room": room_name}
        print(f"Room: {room_name}")

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
        reply = await session.generate_reply(
            instructions="simply greet with namaste and introduce yourself, keep it very simple and short, without think tag, dont think here",
        )
        print("LLM →", reply.chat_items)

    except Exception as e:
        logger.exception("Error in entrypoint")
        raise e
