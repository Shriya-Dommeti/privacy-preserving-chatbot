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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main app background - subtle dark gray/black */
    .stApp {
        background: #101827; /* Dark background color */
    }
    
    /* Main Content Container - Dark/Navy Blue */
    .main .block-container {
        padding: 2rem;
        background: #0D1117; /* Very Dark Container */
        border-radius: 16px;
        box-shadow: 0 0 40px rgba(0, 0, 0, 0.5);
        max-width: 1400px;
    }

    /* Header Styling to match image */
    /* Target the element containing the title and powered-by text */
    div[data-testid="stVerticalBlock"] > div:first-child > div:nth-child(2) {
        background: #1F2937; /* Darker background for the header block */
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Header h1 */
    div[data-testid="stVerticalBlock"] > div:first-child > div:nth-child(2) h1 {
        color: #E5E7EB !important; /* White/Light Gray color */
        font-weight: 700 !important;
        font-size: 32px !important;
        margin-bottom: 5px !important;
        background: none !important;
        -webkit-text-fill-color: unset !important;
    }
    
    /* Header p (Enterprise-Grade Chatbot...) */
    div[data-testid="stVerticalBlock"] > div:first-child > div:nth-child(2) p:nth-child(2) {
        color: #9CA3AF !important; /* Lighter text for subtitle */
        font-size: 16px !important;
        font-weight: 500 !important;
        margin-top: 0 !important;
        margin-bottom: 4px !important;
    }
    
    /* Header p (Powered by...) */
    div[data-testid="stVerticalBlock"] > div:first-child > div:nth-child(2) p:nth-child(3) {
        color: #4B5563 !important; /* Darker text for model name */
        font-size: 13px !important;
        font-weight: 500 !important;
        margin-top: 0 !important;
    }

    /* Chat Messages - Base styling */
    .stChatMessage {
        border-radius: 16px !important;
        padding: 20px !important;
        margin: 12px 0 !important;
        font-size: 17px !important;
        line-height: 1.7 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
        background: #1F2937 !important; /* Ensure a base dark background */
    }
    
    /* User Message - Dark Gradient Purple/Indigo with White Text */
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important; /* Dark Blue/Purple Gradient */
        color: white !important;
        border-radius: 16px 16px 4px 16px !important; /* Squared corner top-right */
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4) !important;
        align-self: flex-end; /* Push to the right */
    }
    
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-user"]) p,
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-user"]) * {
        color: white !important;
        font-weight: 500 !important;
        font-size: 17px !important;
    }
    
    /* Assistant Message - Light Gray/White with Dark Text */
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background: #F3F4F6 !important; /* Light background */
        border: 1px solid #E5E7EB !important;
        color: #1F2937 !important;
        border-radius: 16px 16px 16px 4px !important; /* Squared corner bottom-right */
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
        align-self: flex-start; /* Keep to the left */
    }
    
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-assistant"]) p,
    div[data-testid="stChatMessageContainer"]:has(div[data-testid="chatAvatarIcon-assistant"]) * {
        color: #1F2937 !important; /* Dark text */
        font-weight: 500 !important;
        font-size: 17px !important;
    }
    
    /* All text in chat messages */
    .stChatMessage * {
        font-size: 17px !important;
        line-height: 1.7 !important;
    }
    
    /* Chat Input Container */
    .stChatInputContainer {
        border-top: 2px solid #374151; /* Darker separator */
        padding-top: 1rem;
        background: #0D1117; /* Match main container background */
    }
    
    .stChatInput textarea {
        border: 2px solid #374151 !important;
        background: #1F2937 !important; /* Dark input field */
        color: #E5E7EB !important; /* Light text input */
        border-radius: 12px !important;
        font-size: 16px !important;
        padding: 12px !important;
    }
    
    .stChatInput textarea:focus {
        border-color: #6366F1 !important; /* Purple focus border */
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3) !important;
    }
    
    /* Buttons - Adjusted to dark theme */
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        padding: 12px 32px !important;
        font-size: 15px !important;
    }
    
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4) !important;
    }
    
    .stButton>button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.5) !important;
    }
    
    .stButton>button[kind="secondary"] {
        background: #374151 !important; /* Darker secondary button */
        color: #D1D5DB !important; /* Light text */
        border: 2px solid #4B5563 !important;
    }
    
    /* Sidebar - Left as light theme for contrast/visibility */
    section[data-testid="stSidebar"] {
        background: #F9FAFB !important; /* Light sidebar */
    }
    
    section[data-testid="stSidebar"] h3 {
        color: #1F2937 !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar text */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #374151 !important;
        font-size: 14px !important;
    }
    
    /* Checkbox and Radio labels */
    .stCheckbox label, .stRadio label {
        color: #1F2937 !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    
    /* Header text (inside main block, not the custom header) */
    h1, h2, h3 {
        color: #E5E7EB !important; /* Light text for headings */
    }
    
    /* Markdown text in main area */
    .main .stMarkdown {
        color: #D1D5DB !important; /* Light text for general markdown */
    }
    
    /* Info boxes/Alerts - Status Badge (Success/No Sensitive Data) */
    /* Modifying the appearance of the success alert for the green badge in the image */
    .stSuccess {
        background-color: #1C3228 !important; /* Dark Green background */
        color: #A7F3D0 !important; /* Light green text */
        border-left: 4px solid #10B981 !important;
    }
    
    .stSuccess p, .stSuccess strong {
        color: #A7F3D0 !important;
    }
    
    /* Info Panel - Footer Legend (HIGH/MEDIUM/SAFE) */
    /* Targeting the element before the chat input */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(2) {
        background: #1F2937; /* Dark background for the legend panel */
        border-radius: 12px;
        padding: 15px 10px;
        margin-top: 20px;
        border-top: 2px solid #374151; /* Separator line */
    }
    
    div[data-testid="stVerticalBlock"] > div:nth-last-child(2) p {
        color: #D1D5DB !important;
    }
    
    /* Colors for HIGH/MEDIUM/SAFE text in the footer legend */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(2) strong {
        font-size: 18px !important;
        font-weight: 700 !important;
    }
    
    /* HIGH color */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(2) strong:nth-child(1) { color: #F87171 !important; }
    /* MEDIUM color */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(2) strong:nth-child(2) { color: #FBBF24 !important; }
    /* SAFE color */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(2) strong:nth-child(3) { color: #4ADE80 !important; }
    
    /* Clear Chat Button Position Adjustment */
    div[data-testid="stVerticalBlock"] > div:nth-last-child(2) div[data-testid="stButton"] {
        margin-left: 20px; /* Space out the buttons */
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #6366F1 !important;
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
