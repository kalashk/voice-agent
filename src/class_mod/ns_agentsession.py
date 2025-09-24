############################
# For Noise Supression
############################

from livekit.agents import AgentSession
from pyrnnoise import RNNoise
from livekit import rtc
import logging
import numpy as np

logger = logging.getLogger("agent")

class NoiseSuppressor:
    def __init__(self):
        self.model = RNNoise(sample_rate=48000)

    def process_frame(self, frame: rtc.AudioFrame) -> rtc.AudioFrame:
        pcm = np.frombuffer(frame.data, dtype=np.int16)
        if len(pcm) % 480 != 0:
            return frame
        denoised = np.zeros_like(pcm)
        for i in range(0, len(pcm), 480):
            _, denoised[i:i+480] = self.model.denoise_frame(pcm[i:i+480])
        frame.data[:] = denoised.tobytes()
        return frame

class NSAgentSession(AgentSession):
    async def _forward_audio_task(self) -> None:
        audio_input = self.input.audio
        if audio_input is None:
            return

        suppressor = NoiseSuppressor()

        async for frame in audio_input:
            clean_frame = suppressor.process_frame(frame)
            if self._activity is not None:
                self._activity.push_audio(clean_frame)
