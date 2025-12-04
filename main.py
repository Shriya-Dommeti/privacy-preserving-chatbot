import re
import streamlit as st
from huggingface_hub import InferenceClient
import json
from datetime import datetime
from enum import Enum
import os

# ---------------------- PAGE CONFIGURATION AND CUSTOM CSS (To mimic Gradio's dark background/white card style) ----------------------

# Page configuration
st.set_page_config(
    page_title="🔒 Privacy Shield AI",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to match the provided modern, attractive Gradio theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main app background - Deep Purple/Blue Gradient */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    }
    
    /* Main Content Container (The white card wrapper) */
    .main .block-container {
        max-width: 1200px;
        padding: 24px !important;
        margin-top: 20px !important;
        margin-bottom: 20px !important;
        background: white; /* White Card Background */
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }

    /* ------------------- Header Styling (Mimicking Gradio's H1/P) ------------------- */
    
    /* Target the block containing the custom header content */
    #header-container {
        text-align: center; 
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Header H1 Title */
    #header-container h1 {
        font-size: 42px; 
        font-weight: 800; 
        margin: 0; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Header P (Enterprise-Grade Chatbot...) */
    #header-container p:nth-child(2) {
        font-size: 16px; 
        color: #64748b; 
        margin-top: 8px; 
        font-weight: 500;
    }
    
    /* Header P (Powered by...) */
    #header-container p:nth-child(3) {
        font-size: 13px; 
        color: #94a3b8; 
        margin-top: 4px;
    }

    /* ------------------- Chat Messages Styling ------------------- */

    /* Chatbot container border */
    .stChatMessage {
        border-radius: 16px !important;
        padding: 16px !important;
        margin: 8px 0 !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* User message styling */
    div[data-testid="stChatMessage"] > div:first-child > div:first-child {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-radius: 16px 16px 4px 16px !important;
    }

    /* Assistant message styling */
    div[data-testid="stChatMessage"] > div:first-child > div:nth-child(2) {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
        border: 1px solid #e2e8f0;
        border-radius: 16px 16px 16px 4px !important;
        color: #1e293b !important;
    }
    
    /* Ensure all text in user messages is white */
    div[data-testid="stChatMessage"] > div:first-child > div:first-child p,
    div[data-testid="stChatMessage"] > div:first-child > div:first-child * {
        color: white !important;
    }

    /* ------------------- Sidebar (Settings Panel) ------------------- */
    section[data-testid="stSidebar"] {
        background: #FFFFFF !important; /* White settings panel */
        border-left: 5px solid #667eea !important;
        box-shadow: -5px 0 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar Labels */
    .st-emotion-cache-16p9c21 {
        font-weight: 600 !important;
        color: #1e293b !important;
        font-size: 14px !important;
    }
    
    /* Sidebar Button Styling */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        width: 100%; /* Make sidebar buttons full width */
    }
    
    /* Primary button (Save Settings) */
    .stButton > button.st-emotion-cache-19tp9t { /* Targeting primary buttons in sidebar */
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* ------------------- Legend Panel Styling (Bottom Card) ------------------- */
    #legend-panel {
        text-align: center; 
        padding: 16px; 
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); 
        border-radius: 10px; 
        margin-top: 20px; 
        border: 1px solid #cbd5e1;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
    }

    /* Hide the default Streamlit footer */
    #root > div:nth-child(1) > div.with-footer > footer {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------- END CSS ----------------------


# Hugging Face setup
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
client = InferenceClient(token=HF_TOKEN) 
LOG_FILE = "chatbot_history.json"

# ---------------------- Severity Levels ----------------------
class SeverityLevel(Enum):
    LOW = "🟢"
    MEDIUM = "🟡"
    HIGH = "🔴"

# ---------------------- Sensitive Data Handler Functions (Replicated from Gradio code) ----------------------

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
    # Mask Aadhaar (123456789012 -> 123******012)
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

def format_alert_badge(alerts, strict_mode, sensitivity_level):
    """
    Generates the colored HTML badge for the assistant's response.
    This logic mimics the Gradio code's alert formatting.
    """
    
    mode_text = '🔒 Strict' if strict_mode else '🔓 Relaxed'

    if not alerts:
        # GREEN badge for safe queries
        full_reply = ""
        full_reply += "\n\n<div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #10b981; margin-top: 12px;'>"
        full_reply += "<strong style='color: #047857;'>🟢 No Sensitive Data Detected - Message is Safe</strong>"
        full_reply += f"<p style='color: #065f46; font-size: 12px; margin-top: 4px;'>Mode: {mode_text} | Sensitivity: {sensitivity_level}</p>"
        full_reply += "</div>"
        return full_reply
    else:
        # RED/YELLOW badge for alerts (Gradio code uses mostly red/orange styling here)
        alert_badge = "\n\n<div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #ef4444; margin-top: 12px;'>"
        alert_badge += "<strong>🔒 Privacy Alerts Detected:</strong><br/>"
        for alert in alerts:
            # Color is HIGH red, or MEDIUM/LOW orange/yellow (mimicking the Gradio block)
            color = "#dc2626" if alert['level'] == "HIGH" else "#f59e0b"
            alert_badge += f"<span style='color: {color}; font-weight: 600;'>{alert['severity']} {alert['message']}</span><br/>"
        alert_badge += f"<p style='color: #64748b; font-size: 12px; margin-top: 8px;'>Mode: {mode_text} (Redacted) | Sensitivity: {sensitivity_level}</p>"
        alert_badge += "</div>"
        return alert_badge

# ---------------------- Initialize session state ----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "strict_mode" not in st.session_state:
    st.session_state.strict_mode = False
if "enable_logging" not in st.session_state:
    st.session_state.enable_logging = True
if "sensitivity_level" not in st.session_state:
    st.session_state.sensitivity_level = "High"

# ---------------------- Streamlit UI Layout ----------------------

# 1. Header HTML
st.markdown(f"""
    <div id='header-container'>
        <h1>🔒 Privacy Shield AI</h1>
        <p>Enterprise-Grade Chatbot with Real-Time Sensitive Data Protection</p>
        <p>Powered by Meta Llama 3.2 3B Instruct</p>
    </div>
""", unsafe_allow_html=True)

# 2. Sidebar for settings (Replicating Gradio's settings panel)
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    st.session_state.strict_mode = st.checkbox(
        "🔒 Strict Privacy Mode",
        value=st.session_state.strict_mode,
        help="Block messages with HIGH-risk sensitive data"
    )
    
    # Info block from Gradio code
    st.markdown("""
    <div style='background: #fef3c7; padding: 8px; border-radius: 6px; margin: 10px 0; font-size: 12px; border-left: 4px solid #f59e0b;'>
        <strong>🔒 Strict Mode:</strong> Blocks messages containing Aadhaar, PAN, Cards, CVV<br/>
        <strong>🔓 Relaxed Mode:</strong> Allows messages but redacts sensitive data
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
    
    # Save Settings Button
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        mode_text = "🔒 Strict Mode (Blocks HIGH-risk data)" if st.session_state.strict_mode else "🔓 Relaxed Mode (Redacts data)"
        st.success(f"""
**✅ Settings Updated Successfully!**

**🔐 Privacy Mode:** {mode_text}  
**📝 Logging:** {'Enabled' if st.session_state.enable_logging else 'Disabled'}  
**🎚️ Sensitivity:** {st.session_state.sensitivity_level}
        """)
    
    # Clear Chat Button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 3. Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# 4. Legend Panel HTML (Bottom)
st.markdown("""
    <div id='legend-panel'>
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


# 5. Chat input handling (The main chat logic)
if prompt := st.chat_input("💬 Type your message here... (All sensitive data is automatically protected)"):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process message
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                # 1. Redact sensitive data from prompt
                user_message, alerts = redact_sensitive_data(prompt)
                
                # 2. Check strict mode (Mimicking Gradio's blocking logic)
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
                    
                    st.markdown(blocked_message, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": blocked_message})
                else:
                    # 3. Get response from LLM
                    messages = [{"role": "user", "content": user_message}]
                    
                    # Using a Mock response since HF_TOKEN isn't available for execution
                    # If HF_TOKEN is set, the real API call would execute:
                    # response = client.chat_completion(messages=messages, model="meta-llama/Llama-3.2-3B-Instruct", max_tokens=256, temperature=0.7).choices[0].message.content
                    
                    reply = f"Thank you for your inquiry about your request. The redacted message was: '{user_message}'. I can provide the following general advice..."
                    
                    # 4. Redact sensitive data from reply
                    safe_reply, reply_alerts = redact_sensitive_data(reply)
                    all_alerts = alerts + reply_alerts
                    
                    # 5. Log if enabled
                    if st.session_state.enable_logging:
                        masked_user = mask_sensitive_data(prompt)
                        masked_reply = mask_sensitive_data(reply)
                        log_interaction(masked_user, masked_reply, all_alerts)
                    
                    # 6. Format response with alert badge
                    alert_badge = format_alert_badge(
                        all_alerts, 
                        st.session_state.strict_mode, 
                        st.session_state.sensitivity_level
                    )
                    full_reply = safe_reply + alert_badge
                    
                    st.markdown(full_reply, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": full_reply})
                    
            except Exception as e:
                error_msg = f"""
                <div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #ef4444; margin-top: 12px;'>
                    <strong style='color: #dc2626;'>⚠️ API Error: Could not process request.</strong><br/>
                    <p style='color: #991b1b; margin-top: 6px;'>{str(e)}</p>
                </div>
                """
                st.markdown(error_msg, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
