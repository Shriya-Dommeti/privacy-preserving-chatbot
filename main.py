import re
import streamlit as st
from huggingface_hub import InferenceClient
import os
import json
from datetime import datetime
from enum import Enum

# Hugging Face API token
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# Hugging Face client
client = InferenceClient(token=HF_TOKEN)

LOG_FILE = "chatbot_history.json"

# ---------------------- Page Configuration ----------------------
st.set_page_config(
    page_title="🔒 Privacy Shield AI",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------- Custom CSS ----------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #f8fafc;
}

.main .block-container {
    background: white;
    border-radius: 16px;
    padding: 24px;
    margin: 20px auto;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    max-width: 1400px;
}

/* Header styling */
.header-container {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    border-radius: 12px;
    padding: 32px 24px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px rgba(79, 70, 229, 0.2);
}

.stChatMessage {
    border-radius: 12px !important;
    padding: 16px !important;
    margin: 8px 0 !important;
    background: white !important;
    border: 1px solid #e5e7eb !important;
}

.stChatMessage[data-testid="user-message"] {
    background: white !important;
    color: #1e293b !important;
    border: 1px solid #e5e7eb !important;
}

.stChatMessage[data-testid="assistant-message"] {
    background: white !important;
    color: #1e293b !important;
    border: 1px solid #e5e7eb !important;
}

.stChatMessage p {
    font-size: 15px !important;
    line-height: 1.6 !important;
    color: #334155 !important;
}

/* Chat input */
.stChatInputContainer {
    border-top: 1px solid #e5e7eb;
    padding-top: 16px;
    background: white;
}

/* Buttons */
.stButton>button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    padding: 10px 24px !important;
}

.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important;
}

.stButton>button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4) !important;
}

.stButton>button[kind="secondary"] {
    background: white !important;
    color: #4f46e5 !important;
    border: 2px solid #4f46e5 !important;
}

.stButton>button[kind="secondary"]:hover {
    background: #f5f3ff !important;
}

/* Sidebar */
div[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    padding: 20px;
}

div[data-testid="stSidebar"] * {
    color: white !important;
}

div[data-testid="stSidebar"] .stButton>button {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: white !important;
}

div[data-testid="stSidebar"] .stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
    border: none !important;
}

/* Checkboxes and Radio */
.stCheckbox label, .stRadio label {
    font-weight: 500 !important;
    font-size: 14px !important;
}

div[data-testid="stSidebar"] .stCheckbox label,
div[data-testid="stSidebar"] .stRadio label {
    color: white !important;
}

/* Text inputs */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    padding: 10px !important;
    font-size: 14px !important;
    background: white !important;
}

.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
}

footer {
    visibility: hidden;
}

/* Expander */
.streamlit-expanderHeader {
    background: #f8fafc !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------- Severity Levels ----------------------
class SeverityLevel(Enum):
    LOW = "🟢"
    MEDIUM = "🟡"
    HIGH = "🔴"

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
    # Mask Aadhaar (123456789012 -> 123*****012)
    text = re.sub(r"\b(\d{3})\d{6}(\d{3})\b", r"\1******\2", text)

    # Mask PAN (ABCDE1234F -> ABC**1234*)
    text = re.sub(r"\b([A-Z]{3})[A-Z]{2}(\d{4})[A-Z]\b", r"\1**\2*", text)

    # Mask phone (9876543210 -> 987****210)
    text = re.sub(r"\b(\d{3})\d{4}(\d{3})\b", r"\1****\2", text)

    # Mask card (1234567890123456 -> 1234********3456)
    text = re.sub(r"\b(\d{4})\d{8}(\d{4})\b", r"\1********\2", text)

    # Mask email (john@gmail.com -> j***@gmail.com)
    text = re.sub(r"([a-zA-Z0-9._%+-])[a-zA-Z0-9._%+-]*(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                  r"\1***\2", text)

    return text

def log_interaction(prompt: str, answer: str, alerts: list[dict]):
    """Log interactions with masked data and severity information."""
    masked_prompt = mask_sensitive_data(prompt)
    masked_answer = mask_sensitive_data(answer)
    
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": masked_prompt,
        "answer": masked_answer,
        "alerts": alerts,
        "severity_summary": {
            "high": sum(1 for a in alerts if a.get("level") == "HIGH"),
            "medium": sum(1 for a in alerts if a.get("level") == "MEDIUM"),
            "low": sum(1 for a in alerts if a.get("level") == "LOW")
        }
    }

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(record)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------------- Session State Initialization ----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "strict_mode" not in st.session_state:
    st.session_state.strict_mode = False

if "enable_logging" not in st.session_state:
    st.session_state.enable_logging = True

if "sensitivity_level" not in st.session_state:
    st.session_state.sensitivity_level = "High"

if "show_history" not in st.session_state:
    st.session_state.show_history = False

if "history_data" not in st.session_state:
    st.session_state.history_data = []

# ---------------------- Sidebar Settings ----------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    strict_mode = st.checkbox(
        "🔒 Strict Privacy Mode",
        value=st.session_state.strict_mode,
        help="Block messages with HIGH-risk sensitive data"
    )
    
    st.markdown("""
    <div style='background: #fef3c7; padding: 8px; border-radius: 6px; margin: 10px 0; font-size: 12px; color: #78350f;'>
        <strong>🔒 Strict Mode:</strong> Blocks messages containing Aadhaar, PAN, Cards, CVV<br/>
        <strong>🔓 Relaxed Mode:</strong> Allows messages but redacts sensitive data
    </div>
    """, unsafe_allow_html=True)
    
    enable_logging = st.checkbox(
        "📝 Enable Logging",
        value=st.session_state.enable_logging,
        help="Save conversation history to file"
    )
    
    sensitivity_level = st.radio(
        "🎚️ Sensitivity Level",
        options=["Low", "Medium", "High"],
        index=2,
        help="Detection strictness (affects future updates)"
    )
    
    st.markdown("---")
    
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        st.session_state.strict_mode = strict_mode
        st.session_state.enable_logging = enable_logging
        st.session_state.sensitivity_level = sensitivity_level
        
        mode_text = "🔒 Strict Mode (Blocks HIGH-risk data)" if strict_mode else "🔓 Relaxed Mode (Redacts data)"
        st.success(f"""
        ✅ Settings Updated Successfully!
        
        🔐 Privacy Mode: **{mode_text}**  
        📝 Logging: **{'Enabled' if enable_logging else 'Disabled'}**  
        🎚️ Sensitivity: **{sensitivity_level}**
        """)
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📜 Conversation History")
    
    # View history button
    if st.button("📖 View Full History", use_container_width=True):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                history_data = json.load(f)
            
            if history_data:
                st.session_state.show_history = True
                st.session_state.history_data = history_data
            else:
                st.info("No conversation history found.")
        except (FileNotFoundError, json.JSONDecodeError):
            st.warning("No history file found or file is empty.")
    
    # Download history button
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            history_json = f.read()
        
        st.download_button(
            label="⬇️ Download History JSON",
            data=history_json,
            file_name=f"chatbot_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    except FileNotFoundError:
        pass
    
    # Clear history button
    if st.button("🗑️ Clear History", use_container_width=True):
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
            st.success("History cleared successfully!")
            st.session_state.show_history = False
        else:
            st.info("No history to clear.")

# ---------------------- Main Header ----------------------
st.markdown("""
<div class="header-container">
    <h1 style='font-size: 42px; font-weight: 800; margin: 0; color: white; text-align: center;'>
        🔒 Privacy Shield AI
    </h1>
    <p style='font-size: 16px; color: rgba(255, 255, 255, 0.9); margin-top: 8px; font-weight: 500; text-align: center;'>
        Enterprise-Grade Chatbot with Real-Time Sensitive Data Protection
    </p>
    <p style='font-size: 13px; color: rgba(255, 255, 255, 0.7); margin-top: 4px; text-align: center;'>
        Powered by Meta Llama 3.2 3B Instruct
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------------- Severity Legend ----------------------
st.markdown("""
<div style='text-align: center; padding: 16px; background: white; 
            border-radius: 10px; margin-bottom: 20px; border: 1px solid #e5e7eb;'>
    <div style='display: flex; justify-content: center; gap: 30px; flex-wrap: wrap;'>
        <div>
            <span style='font-size: 24px;'>🔴</span>
            <strong style='color: #dc2626; margin-left: 8px;'>HIGH</strong>
            <p style='color: #64748b; font-size: 13px; margin: 4px 0 0 0;'>Aadhaar, PAN, Cards, CVV</p>
        </div>
        <div>
            <span style='font-size: 24px;'>🟡</span>
            <strong style='color: #f59e0b; margin-left: 8px;'>MEDIUM</strong>
            <p style='color: #64748b; font-size: 13px; margin: 4px 0 0 0;'>Email, Phone, Postal Code</p>
        </div>
        <div>
            <span style='font-size: 24px;'>🟢</span>
            <strong style='color: #10b981; margin-left: 8px;'>SAFE</strong>
            <p style='color: #64748b; font-size: 13px; margin: 4px 0 0 0;'>No Sensitive Data</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------- History Viewer Modal ----------------------
if st.session_state.show_history:
    st.markdown("---")
    st.markdown("### 📜 Conversation History Viewer")
    
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("❌ Close"):
            st.session_state.show_history = False
            st.rerun()
    
    if st.session_state.history_data:
        # Statistics
        total_convos = len(st.session_state.history_data)
        total_high = sum(record.get('severity_summary', {}).get('high', 0) for record in st.session_state.history_data)
        total_medium = sum(record.get('severity_summary', {}).get('medium', 0) for record in st.session_state.history_data)
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 16px; border-radius: 8px; margin-bottom: 20px;'>
            <strong>📊 Statistics</strong><br/>
            <span style='color: #1e40af;'>Total Conversations: {total_convos}</span> | 
            <span style='color: #dc2626;'>🔴 HIGH Alerts: {total_high}</span> | 
            <span style='color: #f59e0b;'>🟡 MEDIUM Alerts: {total_medium}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Display each conversation
        for idx, record in enumerate(reversed(st.session_state.history_data), 1):
            timestamp = record.get('timestamp', 'Unknown')
            prompt = record.get('prompt', '')
            answer = record.get('answer', '')
            alerts = record.get('alerts', [])
            severity_summary = record.get('severity_summary', {})
            
            with st.expander(f"💬 Conversation #{len(st.session_state.history_data) - idx + 1} - {timestamp}", expanded=False):
                st.markdown(f"**🕒 Time:** {timestamp}")
                st.markdown(f"**👤 User:** {prompt}")
                st.markdown(f"**🤖 Assistant:** {answer}")
                
                if alerts:
                    st.markdown("**⚠️ Alerts:**")
                    for alert in alerts:
                        color = "#dc2626" if alert.get('level') == 'HIGH' else "#f59e0b"
                        st.markdown(f"<span style='color: {color};'>{alert.get('severity', '')} {alert.get('message', '')}</span>", unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='background: #f8fafc; padding: 8px; border-radius: 4px; margin-top: 8px; font-size: 12px;'>
                    📊 Summary: 🔴 {severity_summary.get('high', 0)} HIGH | 🟡 {severity_summary.get('medium', 0)} MEDIUM | 🟢 {severity_summary.get('low', 0)} LOW
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")

# ---------------------- Chat Display ----------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# ---------------------- Chat Input and Processing ----------------------
if prompt := st.chat_input("💬 Type your message here... (All sensitive data is automatically protected)"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process message
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Check for sensitive data
            user_message, alerts = redact_sensitive_data(prompt)
            
            # In strict mode, block messages with HIGH severity alerts
            if st.session_state.strict_mode and any(alert['level'] == 'HIGH' for alert in alerts):
                blocked_message = """
                <div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); padding: 16px; border-radius: 8px; border-left: 4px solid #ef4444;'>
                    <strong style='color: #dc2626;'>🚫 Message Blocked - Strict Privacy Mode</strong><br/>
                    <p style='color: #991b1b; margin-top: 8px;'>Your message contains HIGH-risk sensitive data and has been blocked for your protection.</p>
                    <p style='color: #7f1d1d; margin-top: 8px; font-size: 14px;'><strong>Detected:</strong></p>
                """
                for alert in alerts:
                    if alert['level'] == 'HIGH':
                        blocked_message += f"<span style='color: #dc2626;'>{alert['severity']} {alert['message']}</span><br/>"
                blocked_message += "<p style='color: #7f1d1d; margin-top: 8px; font-size: 13px;'><em>💡 Tip: Disable strict mode in settings to allow redacted messages.</em></p>"
                blocked_message += "</div>"
                
                message_placeholder.markdown(blocked_message, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": blocked_message})
            else:
                # Proceed with normal chat
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

                # Log interaction only if logging is enabled
                if st.session_state.enable_logging:
                    masked_user = mask_sensitive_data(prompt)
                    masked_reply = mask_sensitive_data(reply)
                    log_interaction(masked_user, masked_reply, all_alerts)
                
                # Format alerts with severity
                if all_alerts:
                    alert_badge = "\n\n<div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #ef4444; margin-top: 12px;'>"
                    alert_badge += "<strong>🔒 Privacy Alerts Detected:</strong><br/>"
                    for alert in all_alerts:
                        color = "#dc2626" if alert['level'] == "HIGH" else "#f59e0b"
                        alert_badge += f"<span style='color: {color}; font-weight: 600;'>{alert['severity']} {alert['message']}</span><br/>"
                    alert_badge += f"<p style='color: #64748b; font-size: 12px; margin-top: 8px;'>Mode: {'🔒 Strict (Redacted)' if not st.session_state.strict_mode else '🔒 Strict'} | Sensitivity: {st.session_state.sensitivity_level}</p>"
                    alert_badge += "</div>"
                    full_reply = safe_reply + alert_badge
                else:
                    # GREEN badge for safe queries
                    full_reply = safe_reply
                    full_reply += "\n\n<div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #10b981; margin-top: 12px;'>"
                    full_reply += "<strong style='color: #047857;'>🟢 No Sensitive Data Detected - Message is Safe</strong>"
                    full_reply += f"<p style='color: #065f46; font-size: 12px; margin-top: 4px;'>Mode: {'🔓 Relaxed' if not st.session_state.strict_mode else '🔒 Strict'} | Sensitivity: {st.session_state.sensitivity_level}</p>"
                    full_reply += "</div>"

                message_placeholder.markdown(full_reply, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": full_reply})

        except Exception as e:
            error_message = f"⚠️ Error: {str(e)}"
            message_placeholder.markdown(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})
