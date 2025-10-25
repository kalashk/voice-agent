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
            return f"✅ Call initiated to {number}\n\n{data}"
        else:
            return f"❌ Failed: {resp.status_code}\n{resp.text}"
    except Exception as e:
        return f"⚠️ Error: {e}"


def get_call_status() -> str:
    """Poll backend for live call status."""
    try:
        resp = requests.get(f"{SERVER_URL}/latest-call-status", headers=HEADERS, timeout=5)
        data = resp.json()
        status = data.get("status", "idle").capitalize()
        number = data.get("number") or "—"
        emoji = {
            "idle": "💤",
            "initiated": "📞",
            "in_progress": "🟡",
            "completed": "✅",
            "failed": "❌",
        }.get(status.lower(), "❓")
        return f"{emoji} Call {status} — {number}"
    except Exception as e:
        return f"⚠️ Error fetching call status: {e}"

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
        name_in = gr.Textbox(label="Customer Name", placeholder="e.g., Abhishek")
        number_in = gr.Textbox(label="Phone Number", placeholder="e.g., 9987654321")
        gender_in = gr.Radio(["male", "female"], label="Voice Gender", value="male")
        record_in = gr.Checkbox(label="Record Call", value=False)
        call_btn = gr.Button("🚀 Start Call", variant="primary")
        call_output = gr.Textbox(label="Call Response", lines=6, interactive=False)

    with gr.Row():
        call_status_label = gr.Markdown("💤 No ongoing call")

    # Bind call button
    call_btn.click(
        make_call,
        inputs=[name_in, number_in, gender_in, record_in],
        outputs=[call_output]
    )

    # Periodic status refresh using load() instead of Timer
    demo.load(
        check_agent_status,
        outputs=[agent_status_label, agent_details],
        every=5.0
    )

    demo.load(
        get_call_status,
        outputs=[call_status_label],
        every=5.0
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
