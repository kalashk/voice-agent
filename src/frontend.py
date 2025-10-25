# import os

# import gradio as gr
# import requests
# from gradio.themes.base import Base
# from gradio.themes.utils import colors, fonts

# # ==========================
# # CONFIG
# # ==========================
# SERVER_URL = os.getenv("VOICE_AGENT_SERVER", "http://127.0.0.1:8000")
# API_KEY = os.getenv("VOICE_AGENT_API_KEY", "supersecret123")


# # ==========================
# # HELPERS
# # ==========================
# def check_agent_status():
#     try:
#         resp = requests.get(
#             f"{SERVER_URL}/agent-status", headers={"X-API-Key": API_KEY}, timeout=5
#         )
#         data = resp.json()
#         if data.get("running"):
#             return "🟢 Agent is ACTIVE", data
#         else:
#             return "🔴 Agent is INACTIVE", data
#     except Exception as e:
#         return f"⚠️ Error checking agent status: {e}", {}


# def make_call(name, number, gender, record):
#     try:
#         # Room name = phone number
#         payload = {
#             "name": name,
#             "number": number,
#             "gender": gender if gender else None,
#             "record": record,
#             "room_name": number,
#         }

#         resp = requests.post(
#             f"{SERVER_URL}/call",
#             headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
#             json=payload,
#             timeout=15,
#         )
#         if resp.status_code == 200:
#             data = resp.json()
#             return f"✅ Call initiated successfully:\n{data}"
#         else:
#             return f"❌ Failed to start call: {resp.status_code}\n{resp.text}"
#     except Exception as e:
#         return f"⚠️ Error: {e}"


# # ==========================
# # UI
# # ==========================
# custom_theme = Base(
#     primary_hue=colors.indigo,
#     secondary_hue=colors.gray,
#     font=fonts.GoogleFont("Inter"),
# )

# with gr.Blocks(theme=custom_theme, title="Voice Agent Dashboard") as demo:
#     gr.Markdown(
#         """
#         # 🎙️ Voice Agent Dashboard
#         Monitor and control your live voice agent.
#         """
#     )

#     with gr.Row():
#         status_btn = gr.Button("🔍 Check Agent Status", variant="secondary")
#         status_output = gr.Textbox(label="Agent Status", interactive=False)

#     with gr.Accordion("📞 Make a Call", open=True):
#         name_in = gr.Textbox(label="Customer Name", placeholder="e.g., Abhishek")
#         number_in = gr.Textbox(label="Phone Number", placeholder="+919876543210")
#         gender_in = gr.Radio(["male", "female"], label="Voice Gender", value="male")
#         record_in = gr.Checkbox(label="Record Call", value=False)
#         call_btn = gr.Button("Start Call", variant="primary")
#         call_output = gr.Textbox(label="Response", lines=5, interactive=False)

#     status_btn.click(check_agent_status, outputs=[status_output])
#     call_btn.click(make_call, inputs=[name_in, number_in, gender_in, record_in], outputs=[call_output])

# demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
import os

import gradio as gr
import requests
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts

# ==========================
# CONFIG
# ==========================
SERVER_URL = os.getenv("VOICE_AGENT_SERVER", "http://127.0.0.1:8000")
API_KEY = os.getenv("VOICE_AGENT_API_KEY", "supersecret123")

HEADERS = {"X-API-Key": API_KEY}

# Global state to track if call is active
call_active = False

# ==========================
# HELPERS
# ==========================

def check_agent_status() -> tuple[str, str]:
    """Check if the voice agent backend is active."""
    try:
        resp = requests.get(f"{SERVER_URL}/agent-status", headers=HEADERS, timeout=5)
        data = resp.json()
        if data.get("running"):
            return "🟢 **Agent Active**", f"PID: {data.get('pid')}"
        else:
            return "🔴 **Agent Inactive**", "Not running"
    except Exception as e:
        return f"⚠️ Error: {e}", "Unknown"


def make_call(name, number, gender, record):
    """Trigger a new outbound call via backend."""
    global call_active
    try:
        # Ensure +91 prefix
        if not number.startswith("+"):
            number = f"+91{number.strip()}"

        payload = {
            "name": name.strip(),
            "number": number,
            "gender": gender,
            "record": record,
            "room_name": number,
        }

        resp = requests.post(
            f"{SERVER_URL}/call",
            headers={**HEADERS, "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()
            call_active = True  # Activate call tracking
            return (
                f"✅ Call initiated to {number}\n\n{data}",
                gr.update(active=True),  # Activate call timer
                "🔄 **Call In Progress** - Monitoring..."  # Update call status
            )
        else:
            return (
                f"❌ Failed: {resp.status_code}\n{resp.text}",
                gr.update(active=False),
                "❌ Call Failed"
            )
    except Exception as e:
        return (
            f"⚠️ Error: {e}",
            gr.update(active=False),
            "⚠️ Error"
        )


def get_call_status() -> tuple[str, dict]:
    """Poll backend for live call status. Only called when call is active."""
    global call_active

    if not call_active:
        return "💤 No ongoing call", gr.update(active=False)

    try:
        resp = requests.get(f"{SERVER_URL}/latest-call-status", headers=HEADERS, timeout=5)
        data = resp.json()
        status = data.get("status", "idle").lower()
        number = data.get("number") or "—"

        emoji_map = {
            "idle": "💤",
            "initiated": "📞",
            "in_progress": "🟡",
            "completed": "✅",
            "failed": "❌",
        }
        emoji = emoji_map.get(status, "❓")

        # If call is completed or failed, stop polling
        if status in ["completed", "failed", "idle"]:
            call_active = False
            status_text = f"{emoji} Call {status.capitalize()} — {number}"
            return status_text, gr.update(active=False)

        # Call still in progress
        status_text = f"{emoji} Call {status.replace('_', ' ').title()} — {number}"
        return status_text, gr.update(active=True)

    except Exception as e:
        call_active = False
        return f"⚠️ Error fetching call status: {e}", gr.update(active=False)


def refresh_call_status():
    """Wrapper for timer tick that only updates when call is active."""
    global call_active
    if call_active:
        status, timer_update = get_call_status()
        return status, timer_update
    else:
        return "💤 No ongoing call", gr.update(active=False)

# ==========================
# UI
# ==========================
custom_theme = Base(
    primary_hue=colors.indigo,
    secondary_hue=colors.gray,
    font=fonts.GoogleFont("Inter"),
)

with gr.Blocks(theme=custom_theme, title="Voice Agent Dashboard") as demo:
    gr.Markdown(
        """
        # 🎙️ Voice Agent Dashboard
        Manage and monitor your live voice agent.
        """
    )

    with gr.Row():
        agent_status_label = gr.Markdown("⏳ Checking agent...")
        agent_details = gr.Textbox(label="Details", interactive=False)

    gr.Markdown("---")

    with gr.Accordion("📞 Make a Call", open=True):
        with gr.Row():
            with gr.Column(scale=2):
                name_in = gr.Textbox(label="Customer Name", placeholder="e.g., Abhishek Kumar")
                number_in = gr.Textbox(label="Phone Number", placeholder="e.g., 9987654321")
            with gr.Column(scale=1):
                gender_in = gr.Radio(["male", "female"], label="Customer Gender", value="male")
                record_in = gr.Checkbox(label="Record Call", value=False)

        call_btn = gr.Button("🚀 Start Call", variant="primary", size="lg")
        call_output = gr.Textbox(label="Call Response", lines=4, interactive=False)

    gr.Markdown("---")

    with gr.Row():
        with gr.Column():
            call_status_label = gr.Markdown("💤 No ongoing call")
            gr.Markdown("_Updates automatically during active calls_", elem_classes="text-sm text-gray-500")

    # Create timers
    agent_timer = gr.Timer(value=5.0, active=True)  # Always active for agent status
    call_timer = gr.Timer(value=3.0, active=False)  # Only active during calls

    # Bind call button - returns 3 outputs now
    call_btn.click(
        make_call,
        inputs=[name_in, number_in, gender_in, record_in],
        outputs=[call_output, call_timer, call_status_label]
    )

    # Bind agent status timer (always running)
    agent_timer.tick(
        check_agent_status,
        outputs=[agent_status_label, agent_details]
    )

    # Bind call status timer (only runs when call is active)
    call_timer.tick(
        refresh_call_status,
        outputs=[call_status_label, call_timer]
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
