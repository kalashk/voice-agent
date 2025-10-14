from livekit.agents import (
    WorkerOptions,
    cli,
)

from helpers.entrypoint import entrypoint
from helpers.setup_session import prewarm

# --------------------------
#   CLI Runner
# --------------------------

if __name__ == "__main__":
    # Run the worker app with entrypoint and optional prewarm function
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm
        )
    )
