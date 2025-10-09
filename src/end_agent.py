import asyncio
from livekit.agents import cli, WorkerOptions
from livekit.agents import Agent, AgentSession, JobContext, RoomInputOptions
from livekit.plugins import silero, noise_cancellation
from livekit.plugins import sarvam, groq
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents import function_tool

class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="Be friendly. If the user says goodbye, end the call gracefull using the tool: `end_session`.",
            tools=[self.end_session],
        )

    @function_tool()
    async def end_session(self, context):
        """End the LiveKit session politely."""
        await context.session.say("Okay, ending our call. Goodbye!")
        await asyncio.sleep(1)
        await context.session.aclose()
        return "Session closed."

async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=sarvam.STT(
            language="hi-IN",
            model="saarika:v2.5"
        ),
        llm=groq.LLM(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.4,
            tool_choice='auto'
        ),
        tts=sarvam.TTS(
            target_language_code="hi-IN",
            speaker="manisha",
            pace=0.95,
            #enable_preprocessing=True,
        ),
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
