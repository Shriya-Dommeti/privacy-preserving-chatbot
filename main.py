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

# Custom CSS with light attractive backgrounds
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main app background - gradient */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Container background */
    .main .block-container {
        padding: 2rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        max-width: 1400px;
    }
    
    /* Chat Messages - Base styling */
    .stChatMessage {
        border-radius: 16px !important;
        padding: 20px !important;
        margin: 12px 0 !important;
        font-size: 17px !important;
        line-height: 1.7 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* User Message - Purple gradient with white text */
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
        color: black !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin: 12px 0 !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    }
    
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-user"]) p,
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-user"]) * {
        color: white !important;
        font-weight: 500 !important;
        font-size: 17px !important;
    }
    
    /* Assistant Message - Light golden/yellow gradient with dark text */
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
        border: 2px solid #fbbf24 !important;
        color: #1e293b !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin: 12px 0 !important;
        box-shadow: 0 4px 12px rgba(251, 191, 36, 0.2) !important;
    }
    
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-assistant"]) p,
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-assistant"]) * {
        color: #1e293b !important;
        font-weight: 500 !important;
        font-size: 17px !important;
    }
    
    /* All text in chat messages */
    .stChatMessage * {
        font-size: 17px !important;
        line-height: 1.7 !important;
    }
    
    /* Chat Input */
    .stChatInputContainer {
        border-top: 2px solid #e5e7eb;
        padding-top: 1rem;
        background: white;
    }
    
    .stChatInput textarea {
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        font-size: 16px !important;
        color: #1e293b !important;
        padding: 12px !important;
    }
    
    .stChatInput textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Buttons */
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
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #f8fafc !important;
    }
    
    section[data-testid="stSidebar"] h3 {
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar text */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #334155 !important;
        font-size: 14px !important;
    }
    
    /* Checkbox and Radio labels */
    .stCheckbox label, .stRadio label {
        color: #1e293b !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    
    /* Header text */
    h1, h2, h3 {
        color: #1e293b !important;
    }
    
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
        font-size: 42px !important;
    }
    
    /* Markdown text in main area */
    .main .stMarkdown {
        color: #1e293b !important;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 10px !important;
        padding: 16px !important;
    }
    
    /* Success message */
    .stSuccess {
        background-color: #d1fae5 !important;
        color: #065f46 !important;
        border-left: 4px solid #10b981 !important;
    }
    
    .stSuccess p, .stSuccess strong {
        color: #065f46 !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
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
    
    # Create user-friendly timestamp
    timestamp = datetime.utcnow()
    formatted_date = timestamp.strftime("%B %d, %Y")
    formatted_time = timestamp.strftime("%I:%M:%S %p UTC")
    
    # Build alert summary
    alert_summary = []
    for alert in alerts:
        alert_summary.append({
            "type": alert["message"],
            "severity": alert["level"],
            "icon": alert["severity"]
        })
    
    # Get conversation ID
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
        # Try to read existing log
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Check if it's old format (list) or new format (dict)
            if isinstance(data, list):
                # Convert old format to new format
                data = {
                    "metadata": {
                        "application": "Privacy Shield AI Chatbot",
                        "version": "1.0",
                        "description": "Conversation logs with privacy protection and sensitive data redaction",
                        "total_conversations": len(data),
                        "last_updated": ""
                    },
                    "conversations": data
                }
    except (FileNotFoundError, json.JSONDecodeError):
        # Create new log structure
        data = {
            "metadata": {
                "application": "Privacy Shield AI Chatbot",
                "version": "1.0",
                "description": "Conversation logs with privacy protection and sensitive data redaction",
                "total_conversations": 0,
                "last_updated": ""
            },
            "conversations": []
        }

    # Add new conversation
    data["conversations"].append(record)
    data["metadata"]["total_conversations"] = len(data["conversations"])
    data["metadata"]["last_updated"] = f"{formatted_date} at {formatted_time}"

    # Write back to file with pretty formatting
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def format_alert_badge(alerts, mode, sensitivity):
    """Format alerts into HTML badge with high contrast."""
    if alerts:
        alert_html = """
        <div style='background: #fee2e2; padding: 14px 18px; border-radius: 10px; 
                    border-left: 5px solid #dc2626; margin-top: 14px; box-shadow: 0 2px 6px rgba(220, 38, 38, 0.1);'>
            <strong style='color: #991b1b; font-size: 16px;'>🔒 Privacy Alerts Detected:</strong><br/>
            <div style='margin-top: 10px;'>
        """
        for alert in alerts:
            color = "#991b1b" if alert['level'] == "HIGH" else "#b45309"
            alert_html += f"<span style='color: {color}; font-weight: 700; font-size: 15px; display: block; margin: 6px 0;'>{alert['severity']} {alert['message']}</span>"
        alert_html += f"""</div>
            <p style='color: #6b7280; font-size: 13px; margin-top: 10px; font-weight: 600;'>
            Mode: {'🔒 Strict' if mode else '🔓 Relaxed'} | Sensitivity: {sensitivity}
            </p>
        </div>
        """
        return alert_html
    else:
        return f"""
        <div style='background: #d1fae5; padding: 14px 18px; border-radius: 10px; 
                    border-left: 5px solid #10b981; margin-top: 14px; box-shadow: 0 2px 6px rgba(16, 185, 129, 0.1);'>
            <strong style='color: #065f46; font-size: 16px;'>🟢 No Sensitive Data Detected - Message is Safe</strong>
            <p style='color: #047857; font-size: 13px; margin-top: 6px; font-weight: 600;'>
            Mode: {'🔒 Strict' if mode else '🔓 Relaxed'} | Sensitivity: {sensitivity}
            </p>
        </div>
        """

# ---------------------- UI Layout ----------------------
# Header
st.markdown("""
    <div style='text-align: center; padding: 20px; background: white; border-radius: 12px; margin-bottom: 20px;'>
        <h1 style='margin: 0;'>🔒 Privacy Shield AI</h1>
        <p style='font-size: 17px; color: #475569; font-weight: 600; margin-top: 8px;'>
            Enterprise-Grade Chatbot with Real-Time Sensitive Data Protection
        </p>
        <p style='font-size: 14px; color: #64748b; font-weight: 500; margin-top: 4px;'>
            Powered by Meta Llama 3.2 3B Instruct
        </p>
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
    <div style='background: #fef3c7; padding: 10px; border-radius: 8px; margin: 12px 0; 
                border-left: 4px solid #f59e0b;'>
        <p style='color: #92400e; font-size: 13px; font-weight: 600; margin: 0;'>
        <strong style='color: #78350f;'>🔒 Strict Mode:</strong> Blocks messages containing Aadhaar, PAN, Cards, CVV<br/>
        <strong style='color: #78350f;'>🔓 Relaxed Mode:</strong> Allows messages but redacts sensitive data
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state.enable_logging = st.checkbox(
        "📝 Enable Logging",
        value=st.session_state.enable_logging,
        help="Save conversation history to file"
    )
    
    st.session_state.sensitivity_level = st.radio(
        "🎚️ Sensitivity Level",
        options=["Low", "Medium", "High"],
        index=["Low", "Medium", "High"].index(st.session_state.sensitivity_level),
        help="Detection strictness (affects future updates)"
    )
    
    st.markdown("---")
    
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        mode_text = "🔒 Strict Mode (Blocks HIGH-risk data)" if st.session_state.strict_mode else "🔓 Relaxed Mode (Redacts data)"
        st.success(f"""
**✅ Settings Updated Successfully!**

**🔐 Privacy Mode:** {mode_text}  
**📝 Logging:** {'Enabled' if st.session_state.enable_logging else 'Disabled'}  
**🎚️ Sensitivity:** {st.session_state.sensitivity_level}
        """)
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Info panel
st.markdown("""
    <div style='text-align: center; padding: 18px; background: #f1f5f9; 
                border-radius: 12px; margin-bottom: 24px; border: 2px solid #cbd5e1;'>
        <div style='display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;'>
            <div style='text-align: center;'>
                <span style='font-size: 28px;'>🔴</span>
                <p style='margin: 0;'><strong style='color: #dc2626; font-size: 16px;'>HIGH</strong></p>
                <p style='color: #475569; font-size: 13px; margin: 6px 0 0 0; font-weight: 600;'>Aadhaar, PAN, Cards, CVV</p>
            </div>
            <div style='text-align: center;'>
                <span style='font-size: 28px;'>🟡</span>
                <p style='margin: 0;'><strong style='color: #f59e0b; font-size: 16px;'>MEDIUM</strong></p>
                <p style='color: #475569; font-size: 13px; margin: 6px 0 0 0; font-weight: 600;'>Email, Phone, Postal Code</p>
            </div>
            <div style='text-align: center;'>
                <span style='font-size: 28px;'>🟢</span>
                <p style='margin: 0;'><strong style='color: #10b981; font-size: 16px;'>SAFE</strong></p>
                <p style='color: #475569; font-size: 13px; margin: 6px 0 0 0; font-weight: 600;'>No Sensitive Data</p>
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
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process message
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                # Redact sensitive data
                user_message, alerts = redact_sensitive_data(prompt)
                
                # Check strict mode
                if st.session_state.strict_mode and any(alert['level'] == 'HIGH' for alert in alerts):
                    blocked_message = """
                    <div style='background: #fee2e2; padding: 18px; border-radius: 10px; 
                                border-left: 5px solid #dc2626; box-shadow: 0 2px 6px rgba(220, 38, 38, 0.1);'>
                        <strong style='color: #991b1b; font-size: 17px;'>🚫 Message Blocked - Strict Privacy Mode</strong><br/>
                        <p style='color: #7f1d1d; margin-top: 10px; font-size: 15px; font-weight: 500;'>
                        Your message contains HIGH-risk sensitive data and has been blocked for your protection.</p>
                        <p style='color: #7f1d1d; margin-top: 10px; font-size: 15px;'><strong>Detected:</strong></p>
                        <div style='margin-top: 8px;'>
                    """
                    for alert in alerts:
                        if alert['level'] == 'HIGH':
                            blocked_message += f"<span style='color: #991b1b; font-weight: 700; font-size: 15px; display: block; margin: 4px 0;'>{alert['severity']} {alert['message']}</span>"
                    blocked_message += """</div>
                        <p style='color: #78350f; margin-top: 12px; font-size: 14px; font-weight: 600; font-style: italic;'>
                        💡 Tip: Disable strict mode in settings to allow redacted messages.</p>
                    </div>
                    """
                    
                    st.markdown(blocked_message, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": blocked_message})
                else:
                    # Get response from LLM
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
                    
                    # Log if enabled
                    if st.session_state.enable_logging:
                        masked_user = mask_sensitive_data(prompt)
                        masked_reply = mask_sensitive_data(reply)
                        log_interaction(masked_user, masked_reply, all_alerts)
                    
                    # Format response with alerts
                    alert_badge = format_alert_badge(
                        all_alerts, 
                        st.session_state.strict_mode, 
                        st.session_state.sensitivity_level
                    )
                    full_reply = safe_reply + alert_badge
                    
                    st.markdown(full_reply, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": full_reply})
                    
            except Exception as e:
                error_msg = f"⚠️ **Error:** {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
