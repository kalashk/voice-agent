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
PID_FILE = AGENT_DIR / "agent.pid"

def _get_saved_pid() -> Optional[int]:
    """Read the saved PID from file, if present."""
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except ValueError:
            return None
    return None

def _is_agent_running() -> bool:
    """Check if saved PID exists and process is alive."""
    pid = _get_saved_pid()
    if not pid:
        return False
    return psutil.pid_exists(pid)

def _clear_pid_file():
    if PID_FILE.exists():
        PID_FILE.unlink()

@app.post("/start-agent", dependencies=[Depends(verify_api_key)])
async def start_agent():
    """Start the agent via 'uv run src/agent.py dev' if not already running."""
    if _is_agent_running():
        pid = _get_saved_pid()
        return {"status": "already_running", "pid": pid}

    # Ensure agent.py exists
    if not AGENT_SCRIPT.exists():
        raise HTTPException(status_code=500, detail=f"{AGENT_SCRIPT} not found")

    logfile_path = AGENT_DIR / "agent.out.log"
    logfile = open(logfile_path, "ab")

    # Command to run agent
    command = ["uv", "run", "src/agent.py", "dev"]

    try:
        if os.name == "posix":  # Linux/macOS
            proc = subprocess.Popen(
                command,
                cwd=AGENT_DIR.parent,
                stdout=subprocess.PIPE,         # <── use PIPE
                stderr=subprocess.STDOUT,
                preexec_fn=os.setpgrp,
                bufsize=1,                      # line-buffered
                text=True,                      # decode bytes automatically
            )
        else:  # Windows
            proc = subprocess.Popen(
                command,
                cwd=AGENT_DIR,
                stdout=subprocess.PIPE,         # <── use PIPE
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                bufsize=1,
                text=True,
            )

        import threading

        def stream_output(pipe, logfile):
            for line in pipe:
                logfile.write(line.encode())    # save to file
                logfile.flush()
                print(line.rstrip())            # print to console

        threading.Thread(target=stream_output, args=(proc.stdout, logfile), daemon=True).start()

        PID_FILE.write_text(str(proc.pid))
        logger.info("✅ Started agent via uv with PID %s", proc.pid)
        return {"status": "started", "pid": proc.pid}

    except Exception as e:
        logger.exception("❌ Failed to start agent: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to start agent: {str(e)}")


@app.post("/stop-agent", dependencies=[Depends(verify_api_key)])
async def stop_agent():
    """Stop the running agent."""
    pid = _get_saved_pid()
    if not pid or not psutil.pid_exists(pid):
        _clear_pid_file()
        return {"status": "not_running"}

    try:
        if os.name == "posix":
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        else:
            psutil.Process(pid).send_signal(signal.CTRL_BREAK_EVENT)
    except Exception:
        psutil.Process(pid).terminate()

    _clear_pid_file()
    logger.info("🛑 Agent stopped (PID %s)", pid)
    return {"status": "stopped", "pid": pid}


@app.get("/agent-status", dependencies=[Depends(verify_api_key)])
async def agent_status():
    """Check if agent.py is running."""
    pid = _get_saved_pid()
    running = pid is not None and psutil.pid_exists(pid)
    return {"running": running, "pid": pid if running else None}

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
