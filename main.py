import re
import streamlit as st
from huggingface_hub import InferenceClient
import json
from datetime import datetime
from enum import Enum
import os

# ---------------------- PAGE CONFIGURATION AND CUSTOM CSS ----------------------

# Page configuration
st.set_page_config(
    page_title="🔒 Privacy Shield AI",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match the provided dark/light card image
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main app background - Very Dark */
    .stApp {
        background: #141D2D; 
    }
    
    /* Main Content Container - Transparent/Inherit dark background */
    .main .block-container {
        padding: 2rem 2rem 0 2rem; /* Keep padding, but no specific background */
        background: transparent;
        max-width: 1400px;
    }

    /* ------------------- Header Card (White Card) ------------------- */
    
    /* Target the block containing the custom header content */
    div[data-testid="stVerticalBlock"] > div:first-child > div:nth-child(2) {
        background: #FFFFFF !important; /* White background */
        padding: 40px !important;
        border-radius: 12px !important;
        text-align: center !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
        margin-bottom: 30px !important;
    }
    
    /* Header Icon and Title */
    div[data-testid="stVerticalBlock"] > div:first-child > div:nth-child(2) h1 {
        color: #4B5563 !important; /* Light gray color for title */
        font-weight: 800 !important;
        font-size: 38px !important;
        margin-bottom: 10px !important;
        background: none !important;
        -webkit-text-fill-color: unset !important;
    }

    /* Header p (Enterprise-Grade Chatbot...) */
    div[data-testid="stVerticalBlock"] > div:first-child > div:nth-child(2) p:nth-child(2) {
        color: #4B5563 !important; 
        font-size: 16px !important;
        font-weight: 500 !important;
        margin-top: 0 !important;
        margin-bottom: 4px !important;
    }
    
    /* Header p (Powered by...) */
    div[data-testid="stVerticalBlock"] > div:first-child > div:nth-child(2) p:nth-child(3) {
        color: #9CA3AF !important; 
        font-size: 13px !important;
        font-weight: 500 !important;
        margin-top: 0 !important;
    }

    /* ------------------- Legend Card (White Card) ------------------- */
    
    /* Target the block containing the legend panel */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(3) {
        background: #FFFFFF !important; /* White background for the legend panel */
        border-radius: 12px !important;
        padding: 20px 30px !important;
        margin-bottom: 30px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
        border: none !important; /* Remove any border */
    }
    
    /* Center the content of the legend card */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(3) > div > div {
        justify-content: center !important;
    }

    /* Legend Text Styling */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(3) p {
        color: #4B5563 !important; /* Dark text */
        font-weight: 600 !important;
        margin-bottom: 0 !important;
    }
    
    /* Legend Severity Bolding/Colors */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(3) strong {
        font-size: 16px !important;
        font-weight: 700 !important;
    }
    
    /* HIGH color */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(3) span:nth-child(1) { color: #EF4444 !important; }
    /* MEDIUM color */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(3) span:nth-child(2) { color: #F59E0B !important; }
    /* SAFE color */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(3) span:nth-child(3) { color: #10B981 !important; }

    /* ------------------- Chat Messages (Hidden in Image) ------------------- */
    /* Since the image only shows the header and legend, we keep the chat bubbles minimal */

    .stChatMessage {
        border-radius: 16px !important;
        padding: 20px !important;
        margin: 12px 0 !important;
        font-size: 17px !important;
        line-height: 1.7 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
        background: #2D3748 !important; /* Dark background for visibility */
        color: white !important;
    }
    
    .stChatMessage p, .stChatMessage * {
        color: white !important;
    }

    /* ------------------- Chat Input (Dark, Full Width Bottom) ------------------- */
    
    .stChatInputContainer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 10px 2rem; 
        background: #141D2D; /* Match app background */
        border-top: none;
        box-shadow: 0 -4px 10px rgba(0, 0, 0, 0.5); 
        z-index: 1000;
    }
    
    /* Center the chat input element itself within the container */
    .stChatInputContainer > div {
        max-width: 1400px; /* Match main content width */
        margin: 0 auto;
        padding-bottom: 10px;
    }
    
    .stChatInput textarea {
        border: none !important; /* Remove borders */
        background: #2D3748 !important; /* Dark input field */
        color: #E5E7EB !important; /* Light text input */
        border-radius: 8px !important;
        font-size: 16px !important;
        padding: 12px 18px !important;
    }
    
    /* The image shows a different button/send icon area */
    /* We'll hide the standard send button to match the minimalist look */
    .stChatInput > form > div > div:last-child {
        display: none !important;
    }
    
    /* Custom styling for the prompt placeholder text */
    .stChatInput textarea::placeholder {
        color: #9CA3AF !important;
        font-style: italic;
    }

    /* ------------------- Other Elements ------------------- */
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #F9FAFB !important; /* Keep sidebar light */
    }
    
    /* Hide the default Streamlit footer */
    #root > div:nth-child(1) > div.with-footer > footer {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------- END CSS ----------------------


# ---------------------- Remaining Code (Unchanged) ----------------------

# Hugging Face setup
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
# Note: InferenceClient is only initialized if needed, but keeping the setup here.
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

# ---------------------- Sensitive Data Handler Functions (Keep as is) ----------------------

# (redact_sensitive_data, mask_sensitive_data, log_interaction, and format_alert_badge should be here)
# **NOTE:** I'm inserting the final requested version of format_alert_badge here for completeness.

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
    """Format alerts into HTML badge with high contrast, matching the dark theme,
       where the badge color is determined by the highest severity level detected."""
    
    mode_text = '🔒 Strict' if mode else '🔓 Relaxed'
    
    # 1. Determine the highest severity level
    highest_severity = "SAFE"
    if alerts:
        # Priority: HIGH > MEDIUM > LOW
        if any(alert['level'] == 'HIGH' for alert in alerts):
            highest_severity = "HIGH"
        elif any(alert['level'] == 'MEDIUM' for alert in alerts):
            highest_severity = "MEDIUM"
        elif any(alert['level'] == 'LOW' for alert in alerts):
            highest_severity = "LOW"

    # 2. Define colors based on the highest severity
    if highest_severity == "HIGH":
        # Red/Dark Red theme
        badge_bg = "#3a1919"
        badge_border = "#F87171"
        badge_title_color = "#FCA5A5"
        badge_text_color = "#FCA5A5"
        alert_msg_title = "🔒 High-Risk Privacy Alerts Detected:"
    elif highest_severity == "MEDIUM":
        # Yellow/Dark Yellow theme
        badge_bg = "#4a3219"
        badge_border = "#FBBF24"
        badge_title_color = "#FCD34D"
        badge_text_color = "#FCD34D"
        alert_msg_title = "🟡 Medium-Risk Privacy Alerts Detected:"
    elif highest_severity == "LOW":
        # Green/Dark Green theme (same as SAFE, but for LOW alerts)
        badge_bg = "#1C3228"
        badge_border = "#10B981"
        badge_title_color = "#A7F3D0"
        badge_text_color = "#A7F3D0"
        alert_msg_title = "🟢 Low-Risk Privacy Alerts Detected:"
    else: # SAFE (No alerts)
        # Light Green/Success theme
        return f"""
        <div style='background: #d1fae5; padding: 14px 18px; border-radius: 10px; 
                    border-left: 5px solid #10b981; margin-top: 14px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);'>
            <strong style='color: #065f46; font-size: 16px;'>🟢 No Sensitive Data Detected - Message is Safe</strong>
            <p style='color: #065f46; font-size: 14px; margin-top: 6px; font-weight: 600;'>
            Mode: <span>{mode_text}</span> | Sensitivity: <span>{sensitivity}</span>
            </p>
        </div>
        """

    # 3. Generate the colored alert badge HTML
    alert_html = f"""
    <div style='background: {badge_bg}; padding: 14px 18px; border-radius: 10px; 
                border-left: 5px solid {badge_border}; margin-top: 14px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);'>
        <strong style='color: {badge_title_color}; font-size: 16px;'>{alert_msg_title}</strong><br/>
        <div style='margin-top: 10px;'>
    """
    for alert in alerts:
        # Use the highest_severity text color for all individual alert messages for consistency
        alert_html += f"<span style='color: {badge_text_color}; font-weight: 700; font-size: 15px; display: block; margin: 6px 0;'>{alert['severity']} {alert['message']}</span>"
    
    alert_html += f"""</div>
        <p style='color: #9CA3AF; font-size: 14px; margin-top: 10px; font-weight: 600;'>
        Mode: <span style='color: {badge_text_color};'>{mode_text}</span> | Sensitivity: <span style='color: {badge_text_color};'>{sensitivity}</span>
        </p>
    </div>
    """
    return alert_html

# ---------------------- UI Layout - RESTRUCTURED ----------------------

# 1. Header Card
# This markdown block is now the "Header Card" styling via the CSS above
st.markdown(f"""
    <div style='text-align: center; background: white; border-radius: 12px;'>
        <h1 style='margin: 0;'>🔒 Privacy Shield AI</h1>
        <p style='margin-top: 8px;'>
            Enterprise-Grade Chatbot with Real-Time Sensitive Data Protection
        </p>
        <p style='margin-top: 4px;'>
            Powered by Meta Llama 3.2 3B Instruct
        </p>
    </div>
""", unsafe_allow_html=True)

# 2. Sidebar for settings (Unchanged functionality, styling controlled by CSS)
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

# 3. Legend Card (Info Panel)
# This markdown block is now the "Legend Card" styling via the CSS above
st.markdown("""
    <div style='text-align: center;'>
        <div style='display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;'>
            <div style='text-align: center;'>
                <span style='font-size: 28px;'>🔴</span>
                <p style='margin: 0; margin-bottom: 5px;'><strong style='color: #EF4444;'>HIGH</strong></p>
                <p style='color: #4B5563; font-size: 13px; margin: 0;'>Aadhaar, PAN, Cards, CVV</p>
            </div>
            <div style='text-align: center;'>
                <span style='font-size: 28px;'>🟡</span>
                <p style='margin: 0; margin-bottom: 5px;'><strong style='color: #F59E0B;'>MEDIUM</strong></p>
                <p style='color: #4B5563; font-size: 13px; margin: 0;'>Email, Phone, Postal Code</p>
            </div>
            <div style='text-align: center;'>
                <span style='font-size: 28px;'>🟢</span>
                <p style='margin: 0; margin-bottom: 5px;'><strong style='color: #10B981;'>SAFE</strong></p>
                <p style='color: #4B5563; font-size: 13px; margin: 0;'>No Sensitive Data</p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 4. Display chat messages (Standard Streamlit chat messages)
# Add a spacer to push the messages up from the fixed input
st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True) 

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# 5. Chat input (Fixed position at the bottom via CSS)
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
                    # NOTE: Using custom HTML for the blocked message to match the dark theme
                    blocked_message = """
                    <div style='background: #2D3748; padding: 18px; border-radius: 10px; 
                                border-left: 5px solid #F87171; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);'>
                        <strong style='color: #FCA5A5; font-size: 17px;'>🚫 Message Blocked - Strict Privacy Mode</strong><br/>
                        <p style='color: #9CA3AF; margin-top: 10px; font-size: 15px; font-weight: 500;'>
                        Your message contains HIGH-risk sensitive data and has been blocked for your protection.</p>
                        <p style='color: #FCA5A5; margin-top: 10px; font-size: 15px;'><strong>Detected:</strong></p>
                        <div style='margin-top: 8px;'>
                    """
                    for alert in alerts:
                        if alert['level'] == 'HIGH':
                            blocked_message += f"<span style='color: #FCA5A5; font-weight: 700; font-size: 15px; display: block; margin: 4px 0;'>{alert['severity']} {alert['message']}</span>"
                    blocked_message += """</div>
                        <p style='color: #9CA3AF; margin-top: 12px; font-size: 14px; font-weight: 600; font-style: italic;'>
                        💡 Tip: Disable strict mode in settings to allow redacted messages.</p>
                    </div>
                    """
                    
                    st.markdown(blocked_message, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": blocked_message})
                else:
                    # Get response from LLM
                    messages = [{"role": "user", "content": user_message}]
                    
                    # Mock LLM response since HUGGINGFACE_TOKEN is not available
                    reply = f"Thank you for your inquiry about changing your Aadhaar phone number. Your redacted query was: '{user_message}'. The steps are to visit the official portal, log in, update the phone number, re-enter it, and submit for verification. If you have any further questions, please feel free to ask!"
                    
                    # response = client.chat_completion(
                    #     messages=messages,
                    #     model="meta-llama/Llama-3.2-3B-Instruct",
                    #     max_tokens=256,
                    #     temperature=0.7
                    # )
                    # reply = response.choices[0].message.content
                    
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
                # Use custom dark error message
                error_msg = f"""
                <div style='background: #3a1919; padding: 14px 18px; border-radius: 10px; 
                            border-left: 5px solid #F87171; margin-top: 14px;'>
                    <strong style='color: #FCA5A5; font-size: 16px;'>⚠️ Error: Could not process request.</strong><br/>
                    <p style='color: #9CA3AF; font-size: 14px; margin-top: 6px;'>{str(e)}</p>
                </div>
                """
                st.markdown(error_msg, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
