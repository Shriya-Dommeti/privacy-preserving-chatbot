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
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern dark UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main app background - dark gradient */
    .stApp {
        background: linear-gradient(135deg, #1a1d2e 0%, #2d1b4e 100%);
    }
    
    /* Hide default header */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    
    /* Container background */
    .main .block-container {
        padding: 1.5rem 2rem;
        max-width: 1200px;
    }
    
    /* Custom Header */
    .custom-header {
        text-align: center;
        padding: 2rem 1rem;
        background: rgba(45, 55, 85, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    
    .custom-header h1 {
        color: #a78bfa;
        font-size: 36px;
        font-weight: 800;
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    
    .custom-header p {
        color: #cbd5e1;
        font-size: 15px;
        margin: 8px 0 0 0;
        font-weight: 500;
    }
    
    .custom-header .subtext {
        color: #94a3b8;
        font-size: 13px;
        margin-top: 4px;
    }
    
    /* Chat container */
    .chat-container {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        min-height: 400px;
        max-height: 500px;
        overflow-y: auto;
        margin-bottom: 1rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
    }
    
    /* Chat Messages */
    .stChatMessage {
        background: transparent !important;
        border: none !important;
        padding: 12px 0 !important;
    }
    
    /* User Message */
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        margin: 8px 0 !important;
        margin-left: auto !important;
        max-width: 85% !important;
        float: right !important;
        clear: both !important;
    }
    
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-user"]) p {
        color: white !important;
        font-size: 15px !important;
        margin: 0 !important;
        font-weight: 500 !important;
    }
    
    /* Assistant Message */
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background: rgba(51, 65, 85, 0.9) !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        margin: 8px 0 !important;
        max-width: 85% !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
    }
    
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-assistant"]) p {
        color: #e2e8f0 !important;
        font-size: 15px !important;
        margin: 0 !important;
        line-height: 1.6 !important;
    }
    
    /* Chat Input Container */
    .stChatInputContainer {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    /* Chat Input */
    .stChatInput {
        background: rgba(30, 41, 59, 0.8) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        padding: 0 !important;
    }
    
    .stChatInput textarea {
        background: transparent !important;
        color: #e2e8f0 !important;
        border: none !important;
        font-size: 15px !important;
        padding: 14px 18px !important;
    }
    
    .stChatInput textarea::placeholder {
        color: #94a3b8 !important;
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }
    
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    .stButton button[kind="secondary"] {
        background: rgba(51, 65, 85, 0.8) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Info Panel */
    .info-panel {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
    }
    
    .info-item {
        text-align: center;
        padding: 12px;
    }
    
    .info-item .icon {
        font-size: 32px;
        margin-bottom: 6px;
    }
    
    .info-item .label {
        color: #e2e8f0;
        font-weight: 700;
        font-size: 14px;
        margin: 4px 0;
    }
    
    .info-item .desc {
        color: #94a3b8;
        font-size: 12px;
        font-weight: 500;
    }
    
    /* Alert Boxes */
    .alert-safe {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 12px;
    }
    
    .alert-safe strong {
        color: #34d399 !important;
        font-size: 14px;
    }
    
    .alert-safe p {
        color: #94a3b8 !important;
        font-size: 12px !important;
        margin-top: 4px !important;
    }
    
    .alert-danger {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 12px;
    }
    
    .alert-danger strong {
        color: #f87171 !important;
        font-size: 14px;
    }
    
    .alert-danger p, .alert-danger span {
        color: #fca5a5 !important;
        font-size: 13px !important;
        margin: 4px 0 !important;
    }
    
    .alert-blocked {
        background: rgba(239, 68, 68, 0.2);
        border: 2px solid rgba(239, 68, 68, 0.5);
        border-left: 5px solid #ef4444;
        border-radius: 10px;
        padding: 16px 20px;
    }
    
    .alert-blocked strong {
        color: #fca5a5 !important;
        font-size: 16px !important;
    }
    
    .alert-blocked p {
        color: #fecaca !important;
        font-size: 14px !important;
        margin: 8px 0 !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(30, 41, 59, 0.95) !important;
        backdrop-filter: blur(10px);
    }
    
    section[data-testid="stSidebar"] h3 {
        color: #a78bfa !important;
        font-weight: 700 !important;
    }
    
    section[data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }
    
    section[data-testid="stSidebar"] p {
        color: #94a3b8 !important;
    }
    
    /* Success message */
    .stSuccess {
        background: rgba(16, 185, 129, 0.15) !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        color: #34d399 !important;
    }
    
    .stSuccess p {
        color: #34d399 !important;
    }
    
    /* Error message */
    .stError {
        background: rgba(239, 68, 68, 0.15) !important;
        border: 1px solid rgba(239, 68, 68, 0.4) !important;
        color: #f87171 !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #a78bfa !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(139, 92, 246, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(139, 92, 246, 0.7);
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

# ---------------------- Enhanced Sensitive Data Handler ----------------------
def redact_sensitive_data(text: str) -> tuple[str, list[dict]]:
    """Redacts sensitive data and returns (redacted_text, alerts with severity)."""
    alerts = []

    # 🔴 HIGH: Aadhaar (12 digits)
    if re.search(r"\b\d{12}\b", text):
        alerts.append({
            "severity": SeverityLevel.HIGH.value,
            "message": "Aadhaar number detected and redacted",
            "level": "HIGH"
        })
        text = re.sub(r"\b\d{12}\b", "[REDACTED_AADHAAR]", text)

    # 🔴 HIGH: PAN Card (ABCDE1234F format)
    if re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text):
        alerts.append({
            "severity": SeverityLevel.HIGH.value,
            "message": "PAN card detected and redacted",
            "level": "HIGH"
        })
        text = re.sub(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "[REDACTED_PAN]", text)

    # 🔴 HIGH: Credit/Debit Card (13-19 digits with optional spaces/dashes)
    if re.search(r"\b(?:\d{4}[\s\-]?){3}\d{1,7}\b", text):
        alerts.append({
            "severity": SeverityLevel.HIGH.value,
            "message": "Card number detected and redacted",
            "level": "HIGH"
        })
        text = re.sub(r"\b(?:\d{4}[\s\-]?){3}\d{1,7}\b", "[REDACTED_CARD]", text)

    # 🔴 HIGH: CVV (3-4 digits preceded by cvv/cvc)
    if re.search(r"\b(?:cvv|cvc)\s*:?\s*\d{3,4}\b", text, re.IGNORECASE):
        alerts.append({
            "severity": SeverityLevel.HIGH.value,
            "message": "CVV detected and redacted",
            "level": "HIGH"
        })
        text = re.sub(r"\b(?:cvv|cvc)\s*:?\s*\d{3,4}\b", "[REDACTED_CVV]", text, flags=re.IGNORECASE)

    # 🟡 MEDIUM: Phone number (10 digits)
    if re.search(r"\b\d{10}\b", text):
        alerts.append({
            "severity": SeverityLevel.MEDIUM.value,
            "message": "Phone number detected and redacted",
            "level": "MEDIUM"
        })
        text = re.sub(r"\b\d{10}\b", "[REDACTED_PHONE]", text)

    # 🟡 MEDIUM: Email
    if re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text):
        alerts.append({
            "severity": SeverityLevel.MEDIUM.value,
            "message": "Email address detected and redacted",
            "level": "MEDIUM"
        })
        text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", text)

    # 🟡 MEDIUM: Address patterns (simplified)
    if re.search(r"\b\d{6}\b", text):
        alerts.append({
            "severity": SeverityLevel.MEDIUM.value,
            "message": "Postal code detected and redacted",
            "level": "MEDIUM"
        })
        text = re.sub(r"\b\d{6}\b", "[REDACTED_PINCODE]", text)

    return text, alerts

def mask_sensitive_data(text: str) -> str:
    """Mask sensitive data for logging (partial visibility)."""
    text = re.sub(r"\b(\d{3})\d{6}(\d{3})\b", r"\1******\2", text)
    text = re.sub(r"\b([A-Z]{3})[A-Z]{2}(\d{4})[A-Z]\b", r"\1**\2*", text)
    text = re.sub(r"\b(\d{3})\d{4}(\d{3})\b", r"\1****\2", text)
    text = re.sub(r"\b(\d{4})\d{8}(\d{4})\b", r"\1********\2", text)
    text = re.sub(r"([a-zA-Z0-9._%+-])[a-zA-Z0-9._%+-]*(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                  r"\1***\2", text)
    return text

def log_interaction(prompt: str, answer: str, alerts: list[dict]):
    """Log interactions with masked data in a user-friendly format."""
    masked_prompt = mask_sensitive_data(prompt)
    masked_answer = mask_sensitive_data(answer)
    
    timestamp = datetime.utcnow()
    formatted_date = timestamp.strftime("%B %d, %Y")
    formatted_time = timestamp.strftime("%I:%M:%S %p UTC")
    
    alert_summary = []
    for alert in alerts:
        alert_summary.append({
            "type": alert["message"],
            "severity": alert["level"],
            "icon": alert["severity"]
        })
    
    conv_id = len(st.session_state.messages) // 2 if st.session_state.messages else 1
    
    record = {
        "conversation_id": conv_id,
        "date": formatted_date,
        "time": formatted_time,
        "timestamp_iso": timestamp.isoformat(),
        "user_message": {
            "original_length": len(prompt),
            "masked_content": masked_prompt,
            "contains_sensitive_data": len(alerts) > 0
        },
        "assistant_response": {
            "original_length": len(answer),
            "masked_content": masked_answer
        },
        "privacy_alerts": {
            "total_count": len(alerts),
            "high_risk_count": sum(1 for a in alerts if a.get("level") == "HIGH"),
            "medium_risk_count": sum(1 for a in alerts if a.get("level") == "MEDIUM"),
            "low_risk_count": sum(1 for a in alerts if a.get("level") == "LOW"),
            "details": alert_summary
        },
        "settings": {
            "strict_mode_enabled": st.session_state.strict_mode,
            "sensitivity_level": st.session_state.sensitivity_level
        }
    }

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                data = {
                    "metadata": {
                        "application": "Privacy Shield AI Chatbot",
                        "version": "1.0",
                        "description": "Conversation logs with privacy protection",
                        "total_conversations": len(data),
                        "last_updated": ""
                    },
                    "conversations": data
                }
    except (FileNotFoundError, json.JSONDecodeError):
        data = {
            "metadata": {
                "application": "Privacy Shield AI Chatbot",
                "version": "1.0",
                "description": "Conversation logs with privacy protection",
                "total_conversations": 0,
                "last_updated": ""
            },
            "conversations": []
        }

    data["conversations"].append(record)
    data["metadata"]["total_conversations"] = len(data["conversations"])
    data["metadata"]["last_updated"] = f"{formatted_date} at {formatted_time}"

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def format_alert_badge(alerts, mode, sensitivity):
    """Format alerts into HTML badge."""
    if alerts:
        alert_html = """<div class='alert-danger'><strong>🔒 Privacy Alerts Detected:</strong><div style='margin-top: 8px;'>"""
        for alert in alerts:
            alert_html += f"<span>{alert['severity']} {alert['message']}</span><br/>"
        alert_html += f"""</div><p style='margin-top: 8px;'>Mode: {'🔒 Strict' if mode else '🔓 Relaxed'} | Sensitivity: {sensitivity}</p></div>"""
        return alert_html
    else:
        return f"""<div class='alert-safe'><strong>🟢 No Sensitive Data Detected - Message is Safe</strong><p>Mode: {'🔒 Strict' if mode else '🔓 Relaxed'} | Sensitivity: {sensitivity}</p></div>"""

# ---------------------- UI Layout ----------------------
# Custom Header
st.markdown("""
<div class='custom-header'>
    <h1>🔒 Privacy Shield AI</h1>
    <p>Enterprise-Grade Chatbot with Real-Time Sensitive Data Protection</p>
    <p class='subtext'>Powered by Meta Llama 3.2 3B Instruct</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    st.session_state.strict_mode = st.checkbox(
        "🔒 Strict Privacy Mode",
        value=st.session_state.strict_mode,
        help="Block messages with HIGH-risk sensitive data"
    )
    
    st.markdown("""
    <div style='background: rgba(245, 158, 11, 0.15); padding: 12px; border-radius: 8px; 
                margin: 12px 0; border-left: 4px solid #f59e0b;'>
        <p style='color: #fbbf24; font-size: 13px; margin: 0;'>
        <strong>🔒 Strict Mode:</strong> Blocks HIGH-risk data<br/>
        <strong>🔓 Relaxed Mode:</strong> Redacts but allows
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state.enable_logging = st.checkbox(
        "📝 Enable Logging",
        value=st.session_state.enable_logging,
        help="Save conversation history"
    )
    
    st.session_state.sensitivity_level = st.radio(
        "🎚️ Sensitivity Level",
        options=["Low", "Medium", "High"],
        index=2,
        help="Detection strictness"
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save", type="primary", use_container_width=True):
            st.success("✅ Settings saved!")
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# Info panel
st.markdown("""
<div class='info-panel'>
    <div style='display: flex; justify-content: space-around; flex-wrap: wrap;'>
        <div class='info-item'>
            <div class='icon'>🔴</div>
            <div class='label'>HIGH</div>
            <div class='desc'>Aadhaar, PAN, Cards, CVV</div>
        </div>
        <div class='info-item'>
            <div class='icon'>🟡</div>
            <div class='label'>MEDIUM</div>
            <div class='desc'>Email, Phone, Postal Code</div>
        </div>
        <div class='info-item'>
            <div class='icon'>🟢</div>
            <div class='label'>SAFE</div>
            <div class='desc'>No Sensitive Data</div>
        </div>
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
                    blocked_message = """<div class='alert-blocked'><strong>🚫 Message Blocked - Strict Privacy Mode</strong><p>Your message contains HIGH-risk sensitive data and has been blocked for your protection.</p><p><strong>Detected:</strong></p><div style='margin-top: 8px;'>"""
                    for alert in alerts:
                        if alert['level'] == 'HIGH':
                            blocked_message += f"<span>{alert['severity']} {alert['message']}</span><br/>"
                    blocked_message += """</div><p style='margin-top: 12px; font-style: italic;'>💡 Tip: Disable strict mode in settings to allow redacted messages.</p></div>"""
                    
                    st.markdown(blocked_message, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": blocked_message})
                else:
                    messages = [{"role": "user", "content": user_message}]
                    response = client.chat_completion(
                        messages=messages,
                        model="meta-llama/Llama-3.2-3B-Instruct",
                        max_tokens=256,
                        temperature=0.7
                    )
                    
                    reply = response.choices[0].message.content
                    safe_reply, reply_alerts = redact_sensitive_data(reply)
                    all_alerts = alerts + reply_alerts
                    
                    if st.session_state.enable_logging:
                        masked_user = mask_sensitive_data(prompt)
                        masked_reply = mask_sensitive_data(reply)
                        log_interaction(masked_user, masked_reply, all_alerts)
                    
                    alert_badge = format_alert_badge(all_alerts, st.session_state.strict_mode, st.session_state.sensitivity_level)
                    full_reply = safe_reply + alert_badge
                    
                    st.markdown(full_reply, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": full_reply})
                    
            except Exception as e:
                error_msg = f"⚠️ **Error:** {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
