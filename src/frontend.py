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


# ==========================
# HELPERS
# ==========================
def check_agent_status():
    try:
        resp = requests.get(
            f"{SERVER_URL}/agent-status", headers={"X-API-Key": API_KEY}, timeout=5
        )
        data = resp.json()
        if data.get("running"):
            return "🟢 Agent is ACTIVE", data
        else:
            return "🔴 Agent is INACTIVE", data
    except Exception as e:
        return f"⚠️ Error checking agent status: {e}", {}


def make_call(name, number, gender, record):
    try:
        # Room name = phone number
        payload = {
            "name": name,
            "number": number,
            "gender": gender if gender else None,
            "record": record,
            "room_name": number,
        }

        resp = requests.post(
            f"{SERVER_URL}/call",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return f"✅ Call initiated successfully:\n{data}"
        else:
            return f"❌ Failed to start call: {resp.status_code}\n{resp.text}"
    except Exception as e:
        return f"⚠️ Error: {e}"


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
        Monitor and control your live voice agent.
        """
    )

    with gr.Row():
        status_btn = gr.Button("🔍 Check Agent Status", variant="secondary")
        status_output = gr.Textbox(label="Agent Status", interactive=False)

    with gr.Accordion("📞 Make a Call", open=True):
        name_in = gr.Textbox(label="Customer Name", placeholder="e.g., Abhishek")
        number_in = gr.Textbox(label="Phone Number", placeholder="+919876543210")
        gender_in = gr.Radio(["male", "female"], label="Voice Gender", value="male")
        record_in = gr.Checkbox(label="Record Call", value=False)
        call_btn = gr.Button("Start Call", variant="primary")
        call_output = gr.Textbox(label="Response", lines=5, interactive=False)

    status_btn.click(check_agent_status, outputs=[status_output])
    call_btn.click(make_call, inputs=[name_in, number_in, gender_in, record_in], outputs=[call_output])

demo.launch(server_name="0.0.0.0", server_port=7860)
