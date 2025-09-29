import os
import logging
import asyncio
import json
from dotenv import load_dotenv
from livekit.agents import (
    JobContext,
    RoomInputOptions,
)
from livekit.agents.llm import LLM
from livekit.plugins import noise_cancellation
from helpers.setup_tts_stt import setup_tts, setup_stt
from helpers.metrics import setup_metrics
from helpers.log_usage import log_usage
from helpers.helpers import load_customer_profile, setup_session
from class_mod.assistant import MyAssistant
from helpers.config import TTS_PROVIDER, STT_PROVIDER, SESSION_LOGS, SESSION_ID

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
        session = setup_session(ctx, setup_stt, setup_tts, STT_PROVIDER, TTS_PROVIDER)

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
                STT_PROVIDER=STT_PROVIDER
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
            room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVCTelephony()),
        )

        # Generate an initial greeting reply (short introduction)
        reply = await session.generate_reply(
            instructions="simply greet with namaste and introduce yourself, keep it simple and short, without think tag, dont think here",
        )
        print("LLM →", reply.chat_items)   # Print AI response to console

        # while True:
        #     # Wait for user input (via STT)
        #     user_input = await session.get_user_input()  # Adjust based on your STT method
        #     if not user_input:
        #         await asyncio.sleep(1)
        #         continue

        #     print(f"User → {user_input}")

        #     # Respond normally with TTS
        #     await session.generate_reply(instructions=user_input)
        #     # Silent LLM check if session should end
        #     llm_instance = assistant.session_ref.llm
        #     if llm_instance and isinstance(llm_instance, LLM):
        #         should_end = await assistant.query_llm_silently(
        #             llm=llm_instance,
        #             prompt="Based on the conversation so far, should the session end? Reply yes or no."
        #         )
        #         if should_end.strip().lower().startswith("yes"):
        #             print("🛑 LLM requested session end")
        #             # Call shutdown safely
        #             shutdown_result = ctx.shutdown(reason="LLM decided to end session")
        #             if asyncio.iscoroutine(shutdown_result):
        #                 await shutdown_result
        #             break
        #     # Silent LLM check if session should end
        #     should_end = await assistant.query_llm_silently(
        #         llm=assistant.session_ref.llm,
        #         prompt=f"Based on the conversation so far, should the session end? Reply yes or no."
        #     )

        #     if should_end.strip().lower().startswith("yes"):
        #         print("🛑 LLM requested session end")
        #         await ctx.shutdown(reason="LLM decided to end session")
        #         break

        #     # Small delay to prevent tight loop
        #     await asyncio.sleep(0.5)

    except Exception as e:
        # Log any errors and re-raise
        logger.exception("Error in entrypoint")
        raise e