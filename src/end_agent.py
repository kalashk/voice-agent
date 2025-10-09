import asyncio
import logging
from dotenv import load_dotenv
from livekit import api
from livekit.agents import cli, WorkerOptions
from livekit.agents import Agent, AgentSession, JobContext, RoomInputOptions, RunContext, get_job_context
from livekit.plugins import silero, noise_cancellation
from livekit.plugins import sarvam, groq, lmnt, deepgram
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents import function_tool

logger = logging.getLogger("agent")
load_dotenv(".env.local")


async def hangup_current_room():
    """Gracefully close the LiveKit room for this job."""
    ctx = get_job_context()
    if ctx is None or ctx.room is None:
        print("⚠️ No active room found. Cannot hang up.")
        return

    room_name = ctx.room.name
    print(f"🛑 Deleting room: {room_name}")

    try:
        await ctx.api.room.delete_room(api.DeleteRoomRequest(room=room_name))
        print(f"✅ Room '{room_name}' deleted successfully.")
    except Exception as e:
        print(f"❌ Failed to delete room: {e}")


class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "You are a resturant reservation assistant. You have called the customer to confirm their reservation. once the reservation is confirmed end the call."
                "speak in short sentences. and keep the conversation engaging and friendly. "
                "If the user says goodbye or wants to end the call, end the call"
            ),
        )

    @function_tool()
    async def end_session(self, context: RunContext):
        """Politely end the LiveKit call for everyone."""
        # Step 1: Say goodbye
        # await context.session.generate_reply(
        #     instructions="Just say have a great day before ending the call. IMP: dont repeat yourself while ending the call."
        # )
        # Step 2: Small pause before hangup
        await asyncio.sleep(5)

        # Step 3: Delete the room (ends SIP + agent)
        await hangup_current_room()

        return "Session ended gracefully."

async def entrypoint(ctx: JobContext):
    logging.basicConfig(level=logging.DEBUG)
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3", 
            language="multi"
        ),
        llm=groq.LLM(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.4,
            tool_choice='auto'
        ),
        tts=lmnt.TTS(
            voice="bella",
            temperature=0.7
        ),
        # tts = sarvam.TTS(
        #     target_language_code="en-IN",
        #     speaker="manisha",
        #     pace=0.95,
        # ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )
    agent = MyAgent()

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    # 🧠 Graceful LLM-driven timeout handler
    async def timeout_close():
        await asyncio.sleep(120)  # 2 minutes
        if session._started:
            print("Session timeout reached — asking LLM to generate closing response.")
            
            # Ask the LLM to generate a natural goodbye message
            await session.generate_reply(
                instructions=(
                    "The session time limit has been reached. "
                    "Politely inform the user that you need to end the call now."
                )
            )

            # Wait 10 seconds for the TTS to finish playing
            await asyncio.sleep(10)
            await session.aclose()

    #asyncio.create_task(timeout_close())

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
