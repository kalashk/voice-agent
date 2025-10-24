import logging
import os
import signal
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    status,
)
from pydantic import BaseModel

from custom_call import run_calls_api  # adjust if needed

app = FastAPI(title="Voice Agent Control API")
logger = logging.getLogger("uvicorn.error")

# ==============================================================
# CONFIG
# ==============================================================

API_KEY = os.getenv("VOICE_AGENT_API_KEY", "supersecret123")  # 🔐 change this or set in .env
AGENT_DIR = str(Path(__file__).parent)
AGENT_PROC = {"proc": None, "cwd": AGENT_DIR}


# ==============================================================
# AUTH MIDDLEWARE
# ==============================================================

def verify_api_key(x_api_key: str = Header(None)):
    """Simple API key check"""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


# ==============================================================
# AGENT PROCESS MANAGEMENT
# ==============================================================

def _is_agent_running():
    p = AGENT_PROC["proc"]
    return p is not None and p.poll() is None


@app.post("/start-agent", dependencies=[Depends(verify_api_key)])
async def start_agent():
    """Start agent.py in background if not already running."""
    if _is_agent_running():
        return {"status": "already_running"}

    agent_path = Path(AGENT_PROC["cwd"]) / "agent.py"
    if not agent_path.exists():
        raise HTTPException(status_code=500, detail=f"{agent_path} not found")

    logfile = open(Path(AGENT_PROC["cwd"]) / "agent.out.log", "ab")  # noqa: SIM115

    # platform-specific subprocess call
    if os.name == "posix":  # macOS/Linux
        proc = subprocess.Popen(
            ["python", str(agent_path)],
            cwd=AGENT_PROC["cwd"],
            stdout=logfile,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setpgrp,
        )
    else:  # Windows fallback
        proc = subprocess.Popen(
            ["python", str(agent_path)],
            cwd=AGENT_PROC["cwd"],
            stdout=logfile,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

    AGENT_PROC["proc"] = proc
    logger.info("✅ Started agent.py with pid %s", proc.pid)
    return {"status": "started", "pid": proc.pid}


@app.post("/stop-agent", dependencies=[Depends(verify_api_key)])
async def stop_agent():
    """Stop the running agent process."""
    if not _is_agent_running():
        return {"status": "not_running"}

    proc = AGENT_PROC["proc"]

    try:
        if os.name == "posix":
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
    except Exception:
        proc.terminate()

    AGENT_PROC["proc"] = None
    logger.info("🛑 Agent stopped")
    return {"status": "stopped"}


@app.get("/agent-status", dependencies=[Depends(verify_api_key)])
async def agent_status():
    running = _is_agent_running()
    pid = AGENT_PROC["proc"].pid if running else None
    return {"running": running, "pid": pid}


# ==============================================================
# CALL HANDLER
# ==============================================================

class CallRequest(BaseModel):
    name: str
    number: str
    gender: Optional[str] = None
    record: Optional[bool] = False
    room_name: Optional[str] = "voice_agent_room"


@app.post("/call", dependencies=[Depends(verify_api_key)])
async def start_call(req: CallRequest, background_tasks: BackgroundTasks):
    """Start a call via agent."""
    if not _is_agent_running():
        raise HTTPException(status_code=400, detail="Agent not running. Call /start-agent first.")

    background_tasks.add_task(_run_call_background, req.dict())
    return {"status": "initiated", "details": req.dict()}


async def _run_call_background(payload: dict):
    try:
        result = await run_calls_api(
            name=payload["name"],
            gender=payload["gender"],
            phone_number=payload["number"],
            room_name=payload.get("room_name", "voice_agent_room"),
            do_record=payload.get("record", False),
        )
        logger.info("📞 Call completed: %s", result)
    except Exception as e:
        logger.exception("❌ Background call failed: %s", e)
