import streamlit as st
import json
import os
import re
from datetime import datetime
from huggingface_hub import InferenceClient
from enum import Enum

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
client = InferenceClient(token=HF_TOKEN)

LOG_FILE = "chatbot_history.json"

class SeverityLevel(Enum):
    LOW = "🟢"
    MEDIUM = "🟡"
    HIGH = "🔴"

# ---------------- Sensitive Data Redaction ---------------
def redact_sensitive_data(text: str):
    alerts = []

    patterns = [
        (r"\b\d{12}\b", "[REDACTED_AADHAAR]", "Aadhaar number detected", "HIGH"),
        (r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "[REDACTED_PAN]", "PAN detected", "HIGH"),
        (r"\b(?:\d{4}[\s\-]?){3}\d{1,7}\b", "[REDACTED_CARD]", "Card number detected", "HIGH"),
        (r"\b(?:cvv|cvc)\s*:?\s*\d{3,4}\b", "[REDACTED_CVV]", "CVV detected", "HIGH"),
        (r"\b\d{10}\b", "[REDACTED_PHONE]", "Phone number detected", "MEDIUM"),
        (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", "Email detected", "MEDIUM"),
        (r"\b\d{6}\b", "[REDACTED_PINCODE]", "Postal code detected", "MEDIUM"),
    ]

    for pattern, repl, msg, level in patterns:
        if re.search(pattern, text):
            alerts.append({
                "severity": SeverityLevel[level].value,
                "message": msg,
                "level": level,
            })
            text = re.sub(pattern, repl, text)

    return text, alerts

# ---------------- Mask for logging ---------------------
def mask_sensitive_data(text: str) -> str:
    text = re.sub(r"\b(\d{3})\d{6}(\d{3})\b", r"\1******\2", text)
    text = re.sub(r"\b([A-Z]{3})[A-Z]{2}(\d{4})[A-Z]\b", r"\1**\2*", text)
    text = re.sub(r"\b(\d{3})\d{4}(\d{3})\b", r"\1****\2", text)
    text = re.sub(r"\b(\d{4})\d{8}(\d{4})\b", r"\1********\2", text)
    text = re.sub(r"([a-zA-Z0-9._%+-])[a-zA-Z0-9._%+-]*(@.*)", r"\1***\2", text)
    return text

def log_interaction(prompt, answer, alerts):
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": mask_sensitive_data(prompt),
        "answer": mask_sensitive_data(answer),
        "alerts": alerts,
    }

    data = []
    if os.path.exists(LOG_FILE):
        try:
            data = json.load(open(LOG_FILE, "r"))
        except:
            pass

    data.append(record)
    json.dump(data, open(LOG_FILE, "w"), indent=4)

# ---------------- STREAMLIT UI -----------------

st.set_page_config(page_title="🔒 Privacy Shield AI", layout="wide")

st.title("🔒 Privacy Shield AI — Streamlit Version")

st.sidebar.header("⚙️ Settings")
strict_mode = st.sidebar.checkbox("Strict Privacy Mode (blocks HIGH risk)", False)
logging_enabled = st.sidebar.checkbox("Enable Logging", True)
sensitivity = st.sidebar.selectbox("Sensitivity Level", ["Low", "Medium", "High"])

# chat input
user_msg = st.chat_input("Type your message...")

if "history" not in st.session_state:
    st.session_state.history = []

# render chat history
for role, content in st.session_state.history:
    with st.chat_message(role):
        st.markdown(content)

if user_msg:
    with st.chat_message("user"):
        st.markdown(user_msg)

    # process redaction
    redacted_msg, alerts = redact_sensitive_data(user_msg)

    if strict_mode and any(a["level"] == "HIGH" for a in alerts):
        reply = "🚫 **Message Blocked (Strict Mode)**\nSensitive data detected."
    else:
        response = client.chat_completion(
            model="meta-llama/Llama-3.2-3B-Instruct",
            messages=[{"role": "user", "content": redacted_msg}],
            max_tokens=256,
        )
        reply = response.choices[0].message.content

    safe_reply, reply_alerts = redact_sensitive_data(reply)
    all_alerts = alerts + reply_alerts

    if logging_enabled:
        log_interaction(user_msg, reply, all_alerts)

    # show assistant response
    with st.chat_message("assistant"):
        st.markdown(safe_reply)

    st.session_state.history.append(("assistant", safe_reply))
