import asyncio
import logging
import os
from typing import Optional

import psutil
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel

from custom_call import run_calls_api  # Import your actual call logic here

# ==============================
# APP CONFIG
# ==============================
app = FastAPI(title="Voice Agent API", version="1.0")

logger = logging.getLogger("uvicorn.error")

API_KEY = os.getenv("VOICE_AGENT_API_KEY", "supersecret123")
AGENT_SCRIPT_NAME = "src/agent.py"
MAX_CONCURRENT_CALLS = 2

# Semaphore for limiting concurrent calls
call_semaphore = asyncio.Semaphore(MAX_CONCURRENT_CALLS)


# ==============================
# AUTH
# ==============================
def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for security."""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


# ==============================
# AGENT STATUS CHECK
# ==============================
def _is_agent_running() -> Optional[int]:
    """Check if agent.py is running and return PID if found."""
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"]
            if cmdline and "agent.py" in " ".join(cmdline):
                return proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


@app.get("/agent-status", dependencies=[Depends(verify_api_key)])
async def agent_status():
    """Return whether the agent is running."""
    pid = _is_agent_running()
    return {"running": pid is not None, "pid": pid}


# ==============================
# CALL HANDLER
# ==============================
class CallRequest(BaseModel):
    name: str
    number: str
    gender: Optional[str] = None
    record: Optional[bool] = False
    room_name: Optional[str] = "voice_agent_room"


@app.post("/call", dependencies=[Depends(verify_api_key)])
async def start_call(req: CallRequest, background_tasks: BackgroundTasks):
    """Initiate a call if agent is running and concurrency limit allows."""
    pid = _is_agent_running()
    if not pid:
        raise HTTPException(
            status_code=400, detail="Agent not running. Please start agent manually."
        )

    # Acquire semaphore slot
    if call_semaphore.locked() and call_semaphore._value <= 0:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum {MAX_CONCURRENT_CALLS} concurrent calls allowed. Try again later.",
        )

    background_tasks.add_task(_run_call_background, req.dict())
    return {"status": "initiated", "details": req.dict()}


async def _run_call_background(payload: dict):
    """Run the call asynchronously with concurrency control."""
    async with call_semaphore:
        try:
            logger.info(f"📞 Starting call: {payload['number']} for {payload['name']}")
            result = await run_calls_api(
                name=payload["name"],
                gender=payload["gender"],
                phone_number=payload["number"],
                room_name=payload.get("room_name", "voice_agent_room"),
                do_record=payload.get("record", False),
            )
            logger.info(f"✅ Call completed: {result}")
        except Exception as e:
            logger.exception(f"❌ Call failed for {payload.get('number')}: {e}")
        finally:
            logger.info(f"🔚 Call finished for {payload.get('number')}")


# ==============================
# HEALTH CHECK
# ==============================
@app.get("/health")
async def health_check():
    """Simple health check for load balancers / monitoring."""
    return {"status": "ok", "uptime_check": True}
