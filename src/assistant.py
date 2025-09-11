import random
import asyncio
from livekit.agents import Agent, AgentSession
from config import THINKING_PROBABILITY
from instructions import get_instructions, THINKING_SNIPPETS


# --------------------------
#   Assistant Definition
# --------------------------
class MyAssistant(Agent):
    """
    Custom Assistant that extends the base LiveKit Agent.
    Plays a random "thinking sound" while the LLM is generating responses.
    """
    def __init__(self, customer_profile: dict, filler_tts, session: AgentSession, **kwargs) -> None:
        instructions = get_instructions(customer_profile)
        super().__init__(instructions=instructions)

        self.customer_profile = customer_profile
        self.filler_tts = filler_tts        # secondary TTS (Cartesia, etc.)
        self.session_ref = session          # session reference for audio publishing

