import logging
import os
import signal
import subprocess
from pathlib import Path
from typing import Optional

import psutil
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel

from custom_call import run_calls_api  # adjust import if needed

app = FastAPI(title="Voice Agent Control API")
logger = logging.getLogger("uvicorn.error")

# ==============================
# CONFIG
# ==============================
API_KEY = os.getenv("VOICE_AGENT_API_KEY", "supersecret123")
AGENT_DIR = Path(__file__).parent
AGENT_SCRIPT = AGENT_DIR / "agent.py"

# ==============================
# AUTH
# ==============================
def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key.")

# ==============================
# AGENT MANAGEMENT
# ==============================
def _get_agent_process():
    """Return the running agent.py process or None."""
    for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
        cmdline = proc.info.get("cmdline")
        if not cmdline:  # skip processes without cmdline
            continue
        try:
            if any("agent.py" in str(part) for part in cmdline):
                return proc
        except Exception:
            continue
    return None


def _is_agent_running():
    return _get_agent_process() is not None

@app.post("/start-agent", dependencies=[Depends(verify_api_key)])
async def start_agent():
    if _is_agent_running():
        proc = _get_agent_process()
        pid = proc.pid if proc else None  # safe, no warning
        return {"status": "already_running", "pid": pid}

    if not AGENT_SCRIPT.exists():
        raise HTTPException(status_code=500, detail=f"{AGENT_SCRIPT} not found")

    logfile = open(AGENT_DIR / "agent.out.log", "ab")  # noqa: SIM115

    # Cross-platform subprocess launch
    if os.name == "posix":
        proc = subprocess.Popen(
            ["python3", str(AGENT_SCRIPT)],
            cwd=AGENT_DIR,
            stdout=logfile,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setpgrp,
        )
    else:  # Windows
        proc = subprocess.Popen(
            ["python", str(AGENT_SCRIPT)],
            cwd=AGENT_DIR,
            stdout=logfile,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

    logger.info("✅ Started agent.py with pid %s", proc.pid)
    return {"status": "started", "pid": proc.pid}

@app.post("/stop-agent", dependencies=[Depends(verify_api_key)])
async def stop_agent():
    proc = _get_agent_process()
    if not proc:
        return {"status": "not_running"}

    try:
        if os.name == "posix":
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
    except Exception:
        proc.terminate()

    logger.info("🛑 Agent stopped (PID %s)", proc.pid)
    return {"status": "stopped", "pid": proc.pid}

@app.get("/agent-status", dependencies=[Depends(verify_api_key)])
async def agent_status():
    proc = _get_agent_process()
    return {"running": proc is not None, "pid": proc.pid if proc else None}

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
