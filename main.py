import re
import streamlit as st
from huggingface_hub import InferenceClient
import json
from datetime import datetime
from enum import Enum
import os

# Page configuration
st.set_page_config(
    page_title="🔒 Privacy Shield AI",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS matching Gradio design exactly
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main app background - Purple gradient like Gradio */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Container background - White card */
    .main .block-container {
        padding: 24px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        max-width: 100%;
        margin: 20px;
    }
    
    /* Chat Messages Base */
    .stChatMessage {
        border-radius: 16px !important;
        padding: 16px !important;
        margin: 8px 0 !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
    }
    
    /* User Message - Purple gradient with white text (matching Gradio) */
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-radius: 16px 16px 4px 16px !important;
        padding: 16px !important;
        margin: 8px 0 !important;
    }
    
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-user"]) p,
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-user"]) * {
        color: white !important;
        font-weight: 500 !important;
        font-size: 16px !important;
    }
    
    /* Assistant Message - Light gray gradient (matching Gradio bot style) */
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
        border: 1px solid #e2e8f0 !important;
        color: #1e293b !important;
        border-radius: 16px 16px 16px 4px !important;
        padding: 16px !important;
        margin: 8px 0 !important;
    }
    
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-assistant"]) p,
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-assistant"]) * {
        color: #1e293b !important;
        font-weight: 500 !important;
        font-size: 16px !important;
    }
    
    /* Chat Input */
    .stChatInputContainer {
        border-top: 2px solid #e5e7eb;
        padding-top: 1rem;
        background: white;
    }
    
    .stChatInput textarea {
        border: 2px solid #e5e7eb !important;
        border-radius: 10px !important;
        font-size: 15px !important;
        color: #1e293b !important;
        padding: 12px !important;
    }
    
    .stChatInput textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Buttons matching Gradio style */
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        padding: 12px 32px !important;
        font-size: 15px !important;
    }
    
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton>button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5) !important;
    }
    
    .stButton>button[kind="secondary"] {
        background: #f1f5f9 !important;
        color: #475569 !important;
        border: 2px solid #e2e8f0 !important;
    }
    
    .stButton>button[kind="secondary"]:hover {
        background: #e2e8f0 !important;
        border-color: #cbd5e1 !important;
    }
    
    /* Sidebar matching Gradio settings panel */
    section[data-testid="stSidebar"] {
        background: #f8fafc !important;
    }
    
    section[data-testid="stSidebar"] h3 {
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: #334155 !important;
        font-size: 14px !important;
    }
    
    .stCheckbox label, .stRadio label {
        color: #1e293b !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Header matching Gradio */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
        font-size: 42px !important;
    }
    
    /* Success message */
    .stSuccess {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%) !important;
        color: #065f46 !important;
        border-left: 4px solid #10b981 !important;
        border-radius: 8px !important;
    }
    
    .stSuccess p, .stSuccess strong {
        color: #065f46 !important;
    }
</style>
""", unsafe_allow_html=True)

# Hugging Face setup
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
client = InferenceClient(token=HF_TOKEN)

LOG_FILE = "chatbot_history.json"

# ---------------------- Severity Levels ----------------------
class SeverityLevel(Enum):
    LOW = "🟢"
    MEDIUM = "🟡"
    HIGH = "🔴"

# ---------------------- Initialize session state ----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "strict_mode" not in st.session_state:
    st.session_state.strict_mode = False
if "enable_logging" not in st.session_state:
    st.session_state.enable_logging = True
if "sensitivity_level" not in st.session_state:
    st.session_state.sensitivity_level = "High"

# ---------------------- Data Handler Functions ----------------------
def redact_sensitive_data(text: str) -> tuple[str, list[dict]]:
    """Redacts sensitive data and returns (redacted_text, alerts with severity)."""
    alerts = []

    if re.search(r"\b\d{12}\b", text):
        alerts.append({"severity": SeverityLevel.HIGH.value, "message": "Aadhaar number detected and redacted", "level": "HIGH"})
        text = re.sub(r"\b\d{12}\b", "[REDACTED_AADHAAR]", text)

    if re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text):
        alerts.append({"severity": SeverityLevel.HIGH.value, "message": "PAN card detected and redacted", "level": "HIGH"})
        text = re.sub(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "[REDACTED_PAN]", text)

    if re.search(r"\b(?:\d{4}[\s\-]?){3}\d{1,7}\b", text):
        alerts.append({"severity": SeverityLevel.HIGH.value, "message": "Card number detected and redacted", "level": "HIGH"})
        text = re.sub(r"\b(?:\d{4}[\s\-]?){3}\d{1,7}\b", "[REDACTED_CARD]", text)

    if re.search(r"\b(?:cvv|cvc)\s*:?\s*\d{3,4}\b", text, re.IGNORECASE):
        alerts.append({"severity": SeverityLevel.HIGH.value, "message": "CVV detected and redacted", "level": "HIGH"})
        text = re.sub(r"\b(?:cvv|cvc)\s*:?\s*\d{3,4}\b", "[REDACTED_CVV]", text, flags=re.IGNORECASE)

    if re.search(r"\b\d{10}\b", text):
        alerts.append({"severity": SeverityLevel.MEDIUM.value, "message": "Phone number detected and redacted", "level": "MEDIUM"})
        text = re.sub(r"\b\d{10}\b", "[REDACTED_PHONE]", text)

    if re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text):
        alerts.append({"severity": SeverityLevel.MEDIUM.value, "message": "Email address detected and redacted", "level": "MEDIUM"})
        text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", text)

    if re.search(r"\b\d{6}\b", text):
        alerts.append({"severity": SeverityLevel.MEDIUM.value, "message": "Postal code detected and redacted", "level": "MEDIUM"})
        text = re.sub(r"\b\d{6}\b", "[REDACTED_PINCODE]", text)

    return text, alerts

def mask_sensitive_data(text: str) -> str:
    """Mask sensitive data for logging."""
    text = re.sub(r"\b(\d{3})\d{6}(\d{3})\b", r"\1******\2", text)
    text = re.sub(r"\b([A-Z]{3})[A-Z]{2}(\d{4})[A-Z]\b", r"\1**\2*", text)
    text = re.sub(r"\b(\d{3})\d{4}(\d{3})\b", r"\1****\2", text)
    text = re.sub(r"\b(\d{4})\d{8}(\d{4})\b", r"\1********\2", text)
    text = re.sub(r"([a-zA-Z0-9._%+-])[a-zA-Z0-9._%+-]*(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", r"\1***\2", text)
    return text

def log_interaction(prompt: str, answer: str, alerts: list[dict]):
    """Log interactions with user-friendly format."""
    masked_prompt = mask_sensitive_data(prompt)
    masked_answer = mask_sensitive_data(answer)
    
    timestamp = datetime.utcnow()
    formatted_date = timestamp.strftime("%B %d, %Y")
    formatted_time = timestamp.strftime("%I:%M:%S %p UTC")
    
    alert_summary = [{"type": a["message"], "severity": a["level"], "icon": a["severity"]} for a in alerts]
    
    record = {
        "conversation_id": len(st.session_state.messages) // 2 if st.session_state.messages else 1,
        "date": formatted_date,
        "time": formatted_time,
        "timestamp_iso": timestamp.isoformat(),
        "user_message": {"original_length": len(prompt), "masked_content": masked_prompt, "contains_sensitive_data": len(alerts) > 0},
        "assistant_response": {"original_length": len(answer), "masked_content": masked_answer},
        "privacy_alerts": {
            "total_count": len(alerts),
            "high_risk_count": sum(1 for a in alerts if a.get("level") == "HIGH"),
            "medium_risk_count": sum(1 for a in alerts if a.get("level") == "MEDIUM"),
            "low_risk_count": sum(1 for a in alerts if a.get("level") == "LOW"),
            "details": alert_summary
        },
        "settings": {"strict_mode_enabled": st.session_state.strict_mode, "sensitivity_level": st.session_state.sensitivity_level}
    }

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                data = {"metadata": {"application": "Privacy Shield AI Chatbot", "version": "1.0", "total_conversations": len(data), "last_updated": ""}, "conversations": data}
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"metadata": {"application": "Privacy Shield AI Chatbot", "version": "1.0", "description": "Conversation logs with privacy protection", "total_conversations": 0, "last_updated": ""}, "conversations": []}

    data["conversations"].append(record)
    data["metadata"]["total_conversations"] = len(data["conversations"])
    data["metadata"]["last_updated"] = f"{formatted_date} at {formatted_time}"

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def format_alert_badge(alerts, mode, sensitivity):
    """Format alerts matching Gradio style."""
    if alerts:
        alert_html = "<div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #ef4444; margin-top: 12px;'>"
        alert_html += "<strong style='color: #dc2626;'>🔒 Privacy Alerts Detected:</strong><br/>"
        for alert in alerts:
            color = "#dc2626" if alert['level'] == "HIGH" else "#f59e0b"
            alert_html += f"<span style='color: {color}; font-weight: 600;'>{alert['severity']} {alert['message']}</span><br/>"
        alert_html += f"<p style='color: #64748b; font-size: 12px; margin-top: 8px;'>Mode: {'🔒 Strict' if mode else '🔓 Relaxed'} | Sensitivity: {sensitivity}</p></div>"
        return alert_html
    else:
        return f"<div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #10b981; margin-top: 12px;'><strong style='color: #047857;'>🟢 No Sensitive Data Detected - Message is Safe</strong><p style='color: #065f46; font-size: 12px; margin-top: 4px;'>Mode: {'🔒 Strict' if mode else '🔓 Relaxed'} | Sensitivity: {sensitivity}</p></div>"

# ---------------------- UI Layout ----------------------
# Header matching Gradio
st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='font-size: 42px; font-weight: 800; margin: 0;'>🔒 Privacy Shield AI</h1>
        <p style='font-size: 16px; color: #64748b; margin-top: 8px; font-weight: 500;'>
            Enterprise-Grade Chatbot with Real-Time Sensitive Data Protection
        </p>
        <p style='font-size: 13px; color: #94a3b8; margin-top: 4px;'>
            Powered by Meta Llama 3.2 3B Instruct
        </p>
    </div>
""", unsafe_allow_html=True)

# Sidebar matching Gradio settings
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    st.session_state.strict_mode = st.checkbox("🔒 Strict Privacy Mode", value=st.session_state.strict_mode, help="Block messages with HIGH-risk sensitive data")
    
    st.markdown("""
    <div style='background: #fef3c7; padding: 8px; border-radius: 6px; margin: 10px 0; font-size: 12px;'>
        <strong>🔒 Strict Mode:</strong> Blocks messages containing Aadhaar, PAN, Cards, CVV<br/>
        <strong>🔓 Relaxed Mode:</strong> Allows messages but redacts sensitive data
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state.enable_logging = st.checkbox("📝 Enable Logging", value=st.session_state.enable_logging, help="Save conversation history to file")
    
    st.session_state.sensitivity_level = st.radio("🎚️ Sensitivity Level", options=["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(st.session_state.sensitivity_level), help="Detection strictness")
    
    st.markdown("---")
    
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        mode_text = "🔒 Strict Mode (Blocks HIGH-risk data)" if st.session_state.strict_mode else "🔓 Relaxed Mode (Redacts data)"
        st.success(f"**✅ Settings Updated!**\n\n**🔐 Privacy Mode:** {mode_text}\n**📝 Logging:** {'Enabled' if st.session_state.enable_logging else 'Disabled'}\n**🎚️ Sensitivity:** {st.session_state.sensitivity_level}")
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Info panel matching Gradio
st.markdown("""
    <div style='text-align: center; padding: 16px; background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); 
                border-radius: 10px; margin-top: 20px; border: 1px solid #cbd5e1; margin-bottom: 20px;'>
        <div style='display: flex; justify-content: center; gap: 30px; flex-wrap: wrap;'>
            <div><span style='font-size: 24px;'>🔴</span>
                <strong style='color: #dc2626; margin-left: 8px;'>HIGH</strong>
                <p style='color: #64748b; font-size: 13px; margin: 4px 0 0 0;'>Aadhaar, PAN, Cards, CVV</p></div>
            <div><span style='font-size: 24px;'>🟡</span>
                <strong style='color: #f59e0b; margin-left: 8px;'>MEDIUM</strong>
                <p style='color: #64748b; font-size: 13px; margin: 4px 0 0 0;'>Email, Phone, Postal Code</p></div>
            <div><span style='font-size: 24px;'>🟢</span>
                <strong style='color: #10b981; margin-left: 8px;'>SAFE</strong>
                <p style='color: #64748b; font-size: 13px; margin: 4px 0 0 0;'>No Sensitive Data</p></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("💬 Type your message here... (All sensitive data is automatically protected)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                user_message, alerts = redact_sensitive_data(prompt)
                
                if st.session_state.strict_mode and any(alert['level'] == 'HIGH' for alert in alerts):
                    blocked_message = "<div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); padding: 16px; border-radius: 8px; border-left: 4px solid #ef4444;'>"
                    blocked_message += "<strong style='color: #dc2626;'>🚫 Message Blocked - Strict Privacy Mode</strong><br/>"
                    blocked_message += "<p style='color: #991b1b; margin-top: 8px;'>Your message contains HIGH-risk sensitive data and has been blocked for your protection.</p>"
                    blocked_message += "<p style='color: #7f1d1d; margin-top: 8px; font-size: 14px;'><strong>Detected:</strong></p>"
                    for alert in alerts:
                        if alert['level'] == 'HIGH':
                            blocked_message += f"<span style='color: #dc2626;'>{alert['severity']} {alert['message']}</span><br/>"
                    blocked_message += "<p style='color: #7f1d1d; margin-top: 8px; font-size: 13px;'><em>💡 Tip: Disable strict mode in settings to allow redacted messages.</em></p></div>"
                    
                    st.markdown(blocked_message, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": blocked_message})
                else:
                    messages = [{"role": "user", "content": user_message}]
                    response = client.chat_completion(messages=messages, model="meta-llama/Llama-3.2-3B-Instruct", max_tokens=256, temperature=0.7)
                    
                    reply = response.choices[0].message.content
                    safe_reply, reply_alerts = redact_sensitive_data(reply)
                    all_alerts = alerts + reply_alerts
                    
                    if st.session_state.enable_logging:
                        log_interaction(mask_sensitive_data(prompt), mask_sensitive_data(reply), all_alerts)
                    
                    alert_badge = format_alert_badge(all_alerts, st.session_state.strict_mode, st.session_state.sensitivity_level)
                    full_reply = safe_reply + alert_badge
                    
                    st.markdown(full_reply, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": full_reply})
                    
            except Exception as e:
                error_msg = f"⚠️ **Error:** {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
