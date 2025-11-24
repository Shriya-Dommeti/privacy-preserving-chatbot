import re
from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from huggingface_hub import InferenceClient
import gradio as gr
from starlette.middleware.cors import CORSMiddleware
import os
import json
from datetime import datetime
from enum import Enum

# Hugging Face API token
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# Hugging Face client
client = InferenceClient(token=HF_TOKEN)

LOG_FILE = "chatbot_history.json"

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

# ---------------------- FastAPI ----------------------
app = FastAPI(title="Privacy-Protected Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return RedirectResponse(url="/gradio")

@app.get("/hello")
def hello():
    return {"reply": "Privacy-Protected Chatbot API is running."}

@app.post("/chat") 
def chat(request: ChatRequest):
    try:
        redacted_user_message, alerts = redact_sensitive_data(request.message)

        # Using Meta Llama model (free tier compatible)
        response = client.text_generation(
            model="meta-llama/Llama-3.2-3B-Instruct",
            prompt=redacted_user_message,
            max_new_tokens=256,
            temperature=0.7
        )

        redacted_reply, reply_alerts = redact_sensitive_data(response)
        all_alerts = alerts + reply_alerts

        masked_user = mask_sensitive_data(request.message)
        masked_reply = mask_sensitive_data(response)
        log_interaction(masked_user, masked_reply, all_alerts)

        return {
            "reply": redacted_reply,
            "alerts": all_alerts,
            "severity_summary": {
                "high": sum(1 for a in all_alerts if a.get("level") == "HIGH"),
                "medium": sum(1 for a in all_alerts if a.get("level") == "MEDIUM")
            }
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/manifest.json")
def manifest():
    return {
        "name": "Privacy Chatbot",
        "short_name": "PrivacyBot",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#1e293b",
        "description": "AI Chatbot with Advanced Privacy Protection"
    }

# ---------------------- Gradio Interface ----------------------
def gradio_chat(message, history, strict_mode, enable_logging, sensitivity_level):
    try:
        # Check for sensitive data first
        user_message, alerts = redact_sensitive_data(message)
        
        # In strict mode, block messages with HIGH severity alerts
        if strict_mode and any(alert['level'] == 'HIGH' for alert in alerts):
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
            
            updated_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": blocked_message}
            ]
            return updated_history
        
        # Proceed with normal chat (relaxed mode or no HIGH alerts)
        # Using Meta Llama 3.2 3B Instruct model
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
        if enable_logging:
            masked_user = mask_sensitive_data(message)
            masked_reply = mask_sensitive_data(reply)
            log_interaction(masked_user, masked_reply, all_alerts)
        
        # Format alerts with severity - GREEN if no sensitive data
        if all_alerts:
            alert_badge = "\n\n<div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #ef4444; margin-top: 12px;'>"
            alert_badge += "<strong>🔒 Privacy Alerts Detected:</strong><br/>"
            for alert in all_alerts:
                color = "#dc2626" if alert['level'] == "HIGH" else "#f59e0b"
                alert_badge += f"<span style='color: {color}; font-weight: 600;'>{alert['severity']} {alert['message']}</span><br/>"
            alert_badge += f"<p style='color: #64748b; font-size: 12px; margin-top: 8px;'>Mode: {'🔒 Strict (Redacted)' if not strict_mode else '🔒 Strict'} | Sensitivity: {sensitivity_level}</p>"
            alert_badge += "</div>"
            full_reply = safe_reply + alert_badge
        else:
            # GREEN badge for safe queries
            full_reply = safe_reply
            full_reply += "\n\n<div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #10b981; margin-top: 12px;'>"
            full_reply += "<strong style='color: #047857;'>🟢 No Sensitive Data Detected - Message is Safe</strong>"
            full_reply += f"<p style='color: #065f46; font-size: 12px; margin-top: 4px;'>Mode: {'🔓 Relaxed' if not strict_mode else '🔒 Strict'} | Sensitivity: {sensitivity_level}</p>"
            full_reply += "</div>"

        # Return properly formatted message list
        updated_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": full_reply}
        ]
        return updated_history

    except Exception as e:
        updated_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": f"⚠️ Error: {str(e)}"}
        ]
        return updated_history

def update_settings(strict_mode, enable_logs, sensitivity_level):
    mode_text = "🔒 Strict Mode (Blocks HIGH-risk data)" if strict_mode else "🔓 Relaxed Mode (Redacts data)"
    settings_msg = f"""
    <div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #10b981;'>
        <strong style='color: #047857;'>✅ Settings Updated Successfully!</strong><br/>
        <p style='color: #065f46; margin-top: 8px;'>
        🔐 Privacy Mode: <strong>{mode_text}</strong><br/>
        📝 Logging: <strong>{'Enabled' if enable_logs else 'Disabled'}</strong><br/>
        🎚️ Sensitivity: <strong>{sensitivity_level}</strong>
        </p>
    </div>
    """
    return settings_msg

# Enhanced CSS for modern, attractive UI
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

.gradio-container {
    max-width: 100% !important;
    padding: 0 !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.contain {
    max-width: 100% !important;
}

.main {
    background: white;
    border-radius: 16px;
    padding: 24px;
    margin: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

#chatbot {
    border-radius: 12px;
    height: 70vh;
    border: 2px solid #e5e7eb;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.message-wrap {
    padding: 16px !important;
    margin: 8px 0 !important;
}

.message-wrap p {
    font-size: 16px !important;
    line-height: 1.6 !important;
    margin: 0 !important;
}

.user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border-radius: 16px 16px 4px 16px !important;
    font-size: 16px !important;
}

.bot {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
    border: 1px solid #e2e8f0;
    border-radius: 16px 16px 16px 4px !important;
    font-size: 16px !important;
}

.user p, .bot p {
    font-size: 16px !important;
    line-height: 1.6 !important;
}

.message {
    font-size: 16px !important;
}

#chatbot .message-wrap .message {
    font-size: 16px !important;
    line-height: 1.6 !important;
}

#component-0 {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    color: white;
    padding: 24px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

#component-0 h1 {
    font-size: 32px;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

label {
    font-weight: 600 !important;
    color: #1e293b !important;
    font-size: 14px !important;
}

.input-wrap textarea {
    border: 2px solid #e5e7eb !important;
    border-radius: 10px !important;
    padding: 12px !important;
    font-size: 15px !important;
    transition: all 0.3s ease !important;
}

.input-wrap textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

.primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px 32px !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
}

.primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5) !important;
}

button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

button:not(.primary) {
    background: #f1f5f9 !important;
    color: #475569 !important;
    border: 2px solid #e2e8f0 !important;
}

button:not(.primary):hover {
    background: #e2e8f0 !important;
    border-color: #cbd5e1 !important;
}

footer {
    display: none !important;
}

.wrap {
    border-radius: 12px !important;
}

#component-2 {
    margin-top: 20px;
}

.settings-button {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
    width: 50px;
    height: 50px;
    border-radius: 50% !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease !important;
}

.settings-button:hover {
    transform: scale(1.1) rotate(90deg) !important;
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.6) !important;
}
"""

# Modern, attractive Gradio interface
with gr.Blocks(css=custom_css, theme=gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="purple",
), title="🔒 Privacy-Protected Chatbot") as gradio_ui:
    
    # Settings state
    settings_visible = gr.State(False)
    
    gr.HTML("""
        <div style='text-align: center; padding: 20px;'>
            <h1 style='font-size: 42px; font-weight: 800; margin: 0; 
                       background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       -webkit-background-clip: text;
                       -webkit-text-fill-color: transparent;
                       background-clip: text;'>
                🔒 Privacy Shield AI
            </h1>
            <p style='font-size: 16px; color: #64748b; margin-top: 8px; font-weight: 500;'>
                Enterprise-Grade Chatbot with Real-Time Sensitive Data Protection
            </p>
            <p style='font-size: 13px; color: #94a3b8; margin-top: 4px;'>
                Powered by Meta Llama 3.2 3B Instruct
            </p>
        </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=5):
            chatbot = gr.Chatbot(
                type="messages",
                height=550,
                show_copy_button=True,
                render_markdown=True,
                bubble_full_width=False
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    label="Your Message",
                    placeholder="💬 Type your message here... (All sensitive data is automatically protected)",
                    lines=2,
                    scale=5,
                    show_label=False
                )
            
            with gr.Row():
                send_btn = gr.Button("🚀 Send Message", variant="primary", scale=2, size="lg")
                clear_btn = gr.Button("🗑️ Clear Chat", scale=1, size="lg")
        
        with gr.Column(scale=1, visible=False) as settings_panel:
            gr.Markdown("### ⚙️ Settings")
            
            strict_privacy = gr.Checkbox(
                label="🔒 Strict Privacy Mode",
                value=False,
                info="Block messages with HIGH-risk sensitive data"
            )
            
            gr.Markdown("""
            <div style='background: #fef3c7; padding: 8px; border-radius: 6px; margin: 10px 0; font-size: 12px;'>
                <strong>🔒 Strict Mode:</strong> Blocks messages containing Aadhaar, PAN, Cards, CVV<br/>
                <strong>🔓 Relaxed Mode:</strong> Allows messages but redacts sensitive data
            </div>
            """)
            
            enable_logging = gr.Checkbox(
                label="📝 Enable Logging",
                value=True,
                info="Save conversation history to file"
            )
            
            sensitivity_level = gr.Radio(
                choices=["Low", "Medium", "High"],
                value="High",
                label="🎚️ Sensitivity Level",
                info="Detection strictness (affects future updates)"
            )
            
            gr.Markdown("---")
            
            save_settings_btn = gr.Button("💾 Save Settings", variant="primary", size="sm")
            
            settings_output = gr.HTML(
                value="",
                visible=False
            )
    
    # Settings toggle button (top right)
    settings_btn = gr.Button(
        "⚙️",
        size="sm",
        elem_classes="settings-button"
    )
    
    gr.HTML("""
        <div style='text-align: center; padding: 16px; background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); 
                    border-radius: 10px; margin-top: 20px; border: 1px solid #cbd5e1;'>
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
    """)
    
    # Event handlers
    def submit_message(message, history, strict, logging, sensitivity):
        return "", gradio_chat(message, history, strict, logging, sensitivity)
    
    def clear_chat():
        return []
    
    def toggle_settings(current_state):
        return not current_state, gr.update(visible=not current_state)
    
    def save_settings(strict, logging, sensitivity):
        msg = update_settings(strict, logging, sensitivity)
        return gr.update(value=msg, visible=True)
    
    msg.submit(submit_message, [msg, chatbot, strict_privacy, enable_logging, sensitivity_level], [msg, chatbot])
    send_btn.click(submit_message, [msg, chatbot, strict_privacy, enable_logging, sensitivity_level], [msg, chatbot])
    clear_btn.click(clear_chat, None, chatbot)
    
    settings_btn.click(
        toggle_settings,
        inputs=[settings_visible],
        outputs=[settings_visible, settings_panel]
    )
    
    save_settings_btn.click(
        save_settings,
        inputs=[strict_privacy, enable_logging, sensitivity_level],
        outputs=[settings_output]
    )

# Mount Gradio to FastAPI
app = gr.mount_gradio_app(app, gradio_ui, path="/gradio")


































# import re
# from fastapi import FastAPI, Query
# from fastapi.responses import RedirectResponse
# from pydantic import BaseModel
# from huggingface_hub import InferenceClient
# import gradio as gr
# from starlette.middleware.cors import CORSMiddleware
# import os
# import json
# from datetime import datetime
# from enum import Enum
# import spacy
# from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
# from presidio_analyzer.nlp_engine import NlpEngineProvider
# from presidio_anonymizer import AnonymizerEngine

# # Hugging Face API token
# HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# # Hugging Face client
# client = InferenceClient(token=HF_TOKEN)

# LOG_FILE = "chatbot_history.json"

# # ---------------------- Initialize NLP Models ----------------------
# try:
#     # Load SpaCy model for English
#     nlp_en = spacy.load("en_core_web_sm")
# except:
#     print("⚠️ SpaCy model not found. Installing...")
#     import subprocess
#     subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
#     nlp_en = spacy.load("en_core_web_sm")

# # Initialize Presidio Analyzer
# configuration = {
#     "nlp_engine_name": "spacy",
#     "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
# }

# provider = NlpEngineProvider(nlp_configuration=configuration)
# nlp_engine = provider.create_engine()

# analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
# anonymizer = AnonymizerEngine()

# # ---------------------- Severity Levels ----------------------
# class SeverityLevel(Enum):
#     LOW = "🟢"
#     MEDIUM = "🟡"
#     HIGH = "🔴"

# # ---------------------- ML/NLP-based PII Detection ----------------------
# def detect_pii_with_presidio(text: str) -> tuple[str, list[dict]]:
#     """Use Presidio to detect contextual PII like names, locations."""
#     alerts = []
    
#     try:
#         # Analyze text with Presidio
#         results = analyzer.analyze(
#             text=text,
#             language="en",
#             entities=["PERSON", "LOCATION", "EMAIL_ADDRESS", "PHONE_NUMBER", 
#                      "CREDIT_CARD", "IBAN_CODE", "US_SSN", "US_PASSPORT"]
#         )
        
#         # Process results
#         for result in results:
#             entity_type = result.entity_type
            
#             if entity_type == "PERSON":
#                 alerts.append({
#                     "severity": SeverityLevel.MEDIUM.value,
#                     "message": f"Person name detected (ML/NLP)",
#                     "level": "MEDIUM"
#                 })
#             elif entity_type == "LOCATION":
#                 alerts.append({
#                     "severity": SeverityLevel.MEDIUM.value,
#                     "message": f"Location/Address detected (ML/NLP)",
#                     "level": "MEDIUM"
#                 })
#             elif entity_type in ["EMAIL_ADDRESS", "PHONE_NUMBER"]:
#                 alerts.append({
#                     "severity": SeverityLevel.MEDIUM.value,
#                     "message": f"{entity_type.replace('_', ' ').title()} detected (ML/NLP)",
#                     "level": "MEDIUM"
#                 })
#             elif entity_type in ["CREDIT_CARD", "US_SSN", "US_PASSPORT"]:
#                 alerts.append({
#                     "severity": SeverityLevel.HIGH.value,
#                     "message": f"{entity_type.replace('_', ' ').title()} detected (ML/NLP)",
#                     "level": "HIGH"
#                 })
        
#         # Anonymize text
#         if results:
#             anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
#             text = anonymized.text
            
#     except Exception as e:
#         print(f"Presidio error: {e}")
    
#     return text, alerts

# def detect_contextual_pii(text: str) -> tuple[str, list[dict]]:
#     """Detect contextual PII like salary, family info, addresses using patterns."""
#     alerts = []
    
#     # Salary detection - Enhanced patterns
#     salary_patterns = [
#         r"(?:salary|income|earning|wages?|compensation|ctc|package)\s*(?:is|of|:|are)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakhs?|lacs?|thousands?|crores?|k|L|lpa)?",
#         r"(?:i\s+(?:earn|make|get|receive))\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakhs?|lacs?|thousands?|crores?|k|L|per\s+(?:month|year|annum))?",
#         r"(?:paid|making|drawing)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakhs?|lacs?|thousands?|crores?|k|L)?",
#     ]
    
#     for pattern in salary_patterns:
#         if re.search(pattern, text, re.IGNORECASE):
#             alerts.append({
#                 "severity": SeverityLevel.HIGH.value,
#                 "message": "Salary/Income information detected (ML/NLP)",
#                 "level": "HIGH"
#             })
#             text = re.sub(pattern, "[REDACTED_SALARY]", text, flags=re.IGNORECASE)
#             break
    
#     # Family information detection - Enhanced patterns
#     family_patterns = [
#         r"(?:mother'?s?|father'?s?|spouse'?s?|wife'?s?|husband'?s?)\s+(?:maiden\s+)?name\s*(?:is|was|:)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
#         r"my\s+(?:mom|dad|wife|husband|mother|father|son|daughter)\s+(?:is\s+)?(?:named|called|known\s+as)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
#         r"(?:mother|father|spouse|wife|husband)\s+name\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
#     ]
    
#     for pattern in family_patterns:
#         if re.search(pattern, text, re.IGNORECASE):
#             alerts.append({
#                 "severity": SeverityLevel.HIGH.value,
#                 "message": "Family member information detected (ML/NLP)",
#                 "level": "HIGH"
#             })
#             text = re.sub(pattern, r"[REDACTED_FAMILY_INFO]", text, flags=re.IGNORECASE)
    
#     # Address detection (contextual) - Enhanced patterns
#     address_patterns = [
#         r"(?:i\s+live\s+(?:at|in|near)|my\s+address\s+is|residing\s+at|located\s+at)\s+([A-Za-z\s,]+(?:Bangalore|Bengaluru|Mumbai|Delhi|Chennai|Hyderabad|Kolkata|Pune|Marathahalli|Whitefield|Koramangala|Indiranagar|HSR\s+Layout)[A-Za-z\s,]*)",
#         r"(?:stay|staying|living)\s+(?:at|in|near)\s+([A-Za-z\s,]+(?:Bangalore|Bengaluru|Mumbai|Delhi|Chennai|Hyderabad|Kolkata|Pune|Marathahalli|Whitefield|Koramangala|Indiranagar|HSR\s+Layout)[A-Za-z\s,]*)",
#         r"(?:house|home|flat|apartment)\s+(?:at|in|near)\s+([A-Za-z\s,]+(?:Bangalore|Bengaluru|Mumbai|Delhi|Chennai|Hyderabad|Kolkata|Pune|Marathahalli|Whitefield|Koramangala|Indiranagar|HSR\s+Layout)[A-Za-z\s,]*)",
#     ]
    
#     for pattern in address_patterns:
#         if re.search(pattern, text, re.IGNORECASE):
#             alerts.append({
#                 "severity": SeverityLevel.MEDIUM.value,
#                 "message": "Residential address detected (ML/NLP)",
#                 "level": "MEDIUM"
#             })
#             text = re.sub(pattern, r"[REDACTED_ADDRESS]", text, flags=re.IGNORECASE)
    
#     # Date of Birth detection
#     dob_patterns = [
#         r"(?:born\s+on|date\s+of\s+birth|dob|birthday\s+is)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
#         r"(?:born\s+on|date\s+of\s+birth|dob|birthday\s+is)\s*:?\s*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})",
#     ]
    
#     for pattern in dob_patterns:
#         if re.search(pattern, text, re.IGNORECASE):
#             alerts.append({
#                 "severity": SeverityLevel.MEDIUM.value,
#                 "message": "Date of birth detected (ML/NLP)",
#                 "level": "MEDIUM"
#             })
#             text = re.sub(pattern, r"[REDACTED_DOB]", text, flags=re.IGNORECASE)
    
#     return text, alerts

# # ---------------------- Enhanced Sensitive Data Handler ----------------------
# def redact_sensitive_data(text: str, use_ml: bool = True) -> tuple[str, list[dict]]:
#     """Redacts sensitive data using regex and optional ML/NLP detection."""
#     all_alerts = []

#     # 1. Regex-based detection (existing - always enabled)
#     # 🔴 HIGH: Aadhaar (12 digits)
#     if re.search(r"\b\d{12}\b", text):
#         all_alerts.append({
#             "severity": SeverityLevel.HIGH.value,
#             "message": "Aadhaar number detected (Regex)",
#             "level": "HIGH"
#         })
#         text = re.sub(r"\b\d{12}\b", "[REDACTED_AADHAAR]", text)

#     # 🔴 HIGH: PAN Card
#     if re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text):
#         all_alerts.append({
#             "severity": SeverityLevel.HIGH.value,
#             "message": "PAN card detected (Regex)",
#             "level": "HIGH"
#         })
#         text = re.sub(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "[REDACTED_PAN]", text)

#     # 🔴 HIGH: Credit/Debit Card
#     if re.search(r"\b(?:\d{4}[\s\-]?){3}\d{1,7}\b", text):
#         all_alerts.append({
#             "severity": SeverityLevel.HIGH.value,
#             "message": "Card number detected (Regex)",
#             "level": "HIGH"
#         })
#         text = re.sub(r"\b(?:\d{4}[\s\-]?){3}\d{1,7}\b", "[REDACTED_CARD]", text)

#     # 🔴 HIGH: CVV
#     if re.search(r"\b(?:cvv|cvc)\s*:?\s*\d{3,4}\b", text, re.IGNORECASE):
#         all_alerts.append({
#             "severity": SeverityLevel.HIGH.value,
#             "message": "CVV detected (Regex)",
#             "level": "HIGH"
#         })
#         text = re.sub(r"\b(?:cvv|cvc)\s*:?\s*\d{3,4}\b", "[REDACTED_CVV]", text, flags=re.IGNORECASE)

#     # 🟡 MEDIUM: Phone number
#     if re.search(r"\b\d{10}\b", text):
#         all_alerts.append({
#             "severity": SeverityLevel.MEDIUM.value,
#             "message": "Phone number detected (Regex)",
#             "level": "MEDIUM"
#         })
#         text = re.sub(r"\b\d{10}\b", "[REDACTED_PHONE]", text)

#     # 🟡 MEDIUM: Email
#     if re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text):
#         all_alerts.append({
#             "severity": SeverityLevel.MEDIUM.value,
#             "message": "Email address detected (Regex)",
#             "level": "MEDIUM"
#         })
#         text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", text)

#     # 🟡 MEDIUM: Postal code
#     if re.search(r"\b\d{6}\b", text):
#         all_alerts.append({
#             "severity": SeverityLevel.MEDIUM.value,
#             "message": "Postal code detected (Regex)",
#             "level": "MEDIUM"
#         })
#         text = re.sub(r"\b\d{6}\b", "[REDACTED_PINCODE]", text)

#     # 2. ML/NLP-based detection (optional - can be toggled)
#     if use_ml:
#         # Presidio detection (names, locations, etc.)
#         text, ml_alerts = detect_pii_with_presidio(text)
#         all_alerts.extend(ml_alerts)
        
#         # Contextual detection (salary, family, addresses)
#         text, context_alerts = detect_contextual_pii(text)
#         all_alerts.extend(context_alerts)

#     return text, all_alerts

# def mask_sensitive_data(text: str) -> str:
#     """Mask sensitive data for logging (partial visibility)."""
#     text = re.sub(r"\b(\d{3})\d{6}(\d{3})\b", r"\1******\2", text)
#     text = re.sub(r"\b([A-Z]{3})[A-Z]{2}(\d{4})[A-Z]\b", r"\1**\2*", text)
#     text = re.sub(r"\b(\d{3})\d{4}(\d{3})\b", r"\1****\2", text)
#     text = re.sub(r"\b(\d{4})\d{8}(\d{4})\b", r"\1********\2", text)
#     text = re.sub(r"([a-zA-Z0-9._%+-])[a-zA-Z0-9._%+-]*(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
#                   r"\1***\2", text)
#     return text

# def log_interaction(prompt: str, answer: str, alerts: list[dict]):
#     """Log interactions with masked data and severity information."""
#     masked_prompt = mask_sensitive_data(prompt)
#     masked_answer = mask_sensitive_data(answer)
    
#     record = {
#         "timestamp": datetime.utcnow().isoformat(),
#         "prompt": masked_prompt,
#         "answer": masked_answer,
#         "alerts": alerts,
#         "severity_summary": {
#             "high": sum(1 for a in alerts if a.get("level") == "HIGH"),
#             "medium": sum(1 for a in alerts if a.get("level") == "MEDIUM"),
#             "low": sum(1 for a in alerts if a.get("level") == "LOW")
#         }
#     }

#     try:
#         with open(LOG_FILE, "r", encoding="utf-8") as f:
#             data = json.load(f)
#     except (FileNotFoundError, json.JSONDecodeError):
#         data = []

#     data.append(record)

#     with open(LOG_FILE, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=4, ensure_ascii=False)

# # ---------------------- FastAPI ----------------------
# app = FastAPI(title="Privacy-Protected Chatbot API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class ChatRequest(BaseModel):
#     message: str

# @app.get("/")
# def root():
#     return RedirectResponse(url="/gradio")

# @app.get("/hello")
# def hello():
#     return {"reply": "Privacy-Protected Chatbot API is running."}

# @app.post("/chat") 
# def chat(request: ChatRequest):
#     try:
#         redacted_user_message, alerts = redact_sensitive_data(request.message)

#         response = client.text_generation(
#             model="meta-llama/Llama-3.2-3B-Instruct",
#             prompt=redacted_user_message,
#             max_new_tokens=256,
#             temperature=0.7
#         )

#         redacted_reply, reply_alerts = redact_sensitive_data(response)
#         all_alerts = alerts + reply_alerts

#         masked_user = mask_sensitive_data(request.message)
#         masked_reply = mask_sensitive_data(response)
#         log_interaction(masked_user, masked_reply, all_alerts)

#         return {
#             "reply": redacted_reply,
#             "alerts": all_alerts,
#             "severity_summary": {
#                 "high": sum(1 for a in all_alerts if a.get("level") == "HIGH"),
#                 "medium": sum(1 for a in all_alerts if a.get("level") == "MEDIUM")
#             }
#         }

#     except Exception as e:
#         return {"error": str(e)}

# @app.get("/manifest.json")
# def manifest():
#     return {
#         "name": "Privacy Chatbot",
#         "short_name": "PrivacyBot",
#         "start_url": "/",
#         "display": "standalone",
#         "background_color": "#0f172a",
#         "theme_color": "#1e293b",
#         "description": "AI Chatbot with Advanced Privacy Protection"
#     }

# # ---------------------- Gradio Interface ----------------------
# def gradio_chat(message, history, strict_mode, enable_logging, sensitivity_level, use_ml):
#     try:
#         # Check for sensitive data with optional ML support
#         user_message, alerts = redact_sensitive_data(message, use_ml=use_ml)
        
#         # In strict mode, block messages with HIGH severity alerts
#         if strict_mode and any(alert['level'] == 'HIGH' for alert in alerts):
#             blocked_message = """
#             <div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); padding: 16px; border-radius: 8px; border-left: 4px solid #ef4444;'>
#                 <strong style='color: #dc2626;'>🚫 Message Blocked - Strict Privacy Mode</strong><br/>
#                 <p style='color: #991b1b; margin-top: 8px;'>Your message contains HIGH-risk sensitive data and has been blocked for your protection.</p>
#                 <p style='color: #7f1d1d; margin-top: 8px; font-size: 14px;'><strong>Detected:</strong></p>
#             """
#             for alert in alerts:
#                 if alert['level'] == 'HIGH':
#                     blocked_message += f"<span style='color: #dc2626;'>{alert['severity']} {alert['message']}</span><br/>"
#             blocked_message += "<p style='color: #7f1d1d; margin-top: 8px; font-size: 13px;'><em>💡 Tip: Disable strict mode in settings to allow redacted messages.</em></p>"
#             blocked_message += "</div>"
            
#             updated_history = history + [
#                 {"role": "user", "content": message},
#                 {"role": "assistant", "content": blocked_message}
#             ]
#             return updated_history
        
#         # Proceed with normal chat
#         messages = [{"role": "user", "content": user_message}]
        
#         response = client.chat_completion(
#             messages=messages,
#             model="meta-llama/Llama-3.2-3B-Instruct",
#             max_tokens=256,
#             temperature=0.7
#         )
        
#         reply = response.choices[0].message.content
#         safe_reply, reply_alerts = redact_sensitive_data(reply, use_ml=use_ml)
#         all_alerts = alerts + reply_alerts

#         # Log interaction only if logging is enabled
#         if enable_logging:
#             masked_user = mask_sensitive_data(message)
#             masked_reply = mask_sensitive_data(reply)
#             log_interaction(masked_user, masked_reply, all_alerts)
        
#         # Format alerts with detection method tags
#         if all_alerts:
#             alert_badge = "\n\n<div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #ef4444; margin-top: 12px;'>"
#             alert_badge += "<strong>🔒 Privacy Alerts Detected:</strong><br/>"
#             for alert in all_alerts:
#                 color = "#dc2626" if alert['level'] == "HIGH" else "#f59e0b"
#                 alert_badge += f"<span style='color: {color}; font-weight: 600;'>{alert['severity']} {alert['message']}</span><br/>"
#             alert_badge += f"<p style='color: #64748b; font-size: 12px; margin-top: 8px;'>Mode: {'🔒 Strict' if strict_mode else '🔓 Relaxed'} | Sensitivity: {sensitivity_level} | ML/NLP: {'✓ Enabled' if use_ml else '✗ Disabled'}</p>"
#             alert_badge += "</div>"
#             full_reply = safe_reply + alert_badge
#         else:
#             full_reply = safe_reply
#             full_reply += "\n\n<div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #10b981; margin-top: 12px;'>"
#             full_reply += "<strong style='color: #047857;'>🟢 No Sensitive Data Detected - Message is Safe</strong>"
#             full_reply += f"<p style='color: #065f46; font-size: 12px; margin-top: 4px;'>Mode: {'🔒 Strict' if strict_mode else '🔓 Relaxed'} | ML/NLP: {'✓ Enabled' if use_ml else '✗ Disabled'}</p>"
#             full_reply += "</div>"

#         updated_history = history + [
#             {"role": "user", "content": message},
#             {"role": "assistant", "content": full_reply}
#         ]
#         return updated_history

#     except Exception as e:
#         updated_history = history + [
#             {"role": "user", "content": message},
#             {"role": "assistant", "content": f"⚠️ Error: {str(e)}"}
#         ]
#         return updated_history

# def update_settings(strict_mode, enable_logs, sensitivity_level, use_ml):
#     mode_text = "🔒 Strict Mode (Blocks HIGH-risk data)" if strict_mode else "🔓 Relaxed Mode (Redacts data)"
#     ml_text = "✅ Enabled (SpaCy + Presidio)" if use_ml else "❌ Disabled (Regex only)"
    
#     settings_msg = f"""
#     <div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #10b981;'>
#         <strong style='color: #047857;'>✅ Settings Updated Successfully!</strong><br/>
#         <p style='color: #065f46; margin-top: 8px;'>
#         🔐 Privacy Mode: <strong>{mode_text}</strong><br/>
#         📝 Logging: <strong>{'Enabled' if enable_logs else 'Disabled'}</strong><br/>
#         🎚️ Sensitivity: <strong>{sensitivity_level}</strong><br/>
#         🤖 ML/NLP Detection: <strong>{ml_text}</strong>
#         </p>
#     </div>
#     """
#     return settings_msg

# # Enhanced CSS
# custom_css = """
# @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

# * {
#     font-family: 'Inter', sans-serif;
# }

# .gradio-container {
#     max-width: 100% !important;
#     padding: 0 !important;
#     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
# }

# .contain {
#     max-width: 100% !important;
# }

# .main {
#     background: white;
#     border-radius: 16px;
#     padding: 24px;
#     margin: 20px;
#     box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
# }

# #chatbot {
#     border-radius: 12px;
#     height: 70vh;
#     border: 2px solid #e5e7eb;
#     box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
# }

# .message-wrap {
#     padding: 16px !important;
#     margin: 8px 0 !important;
# }

# .message-wrap p {
#     font-size: 16px !important;
#     line-height: 1.6 !important;
#     margin: 0 !important;
# }

# .user {
#     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
#     color: white !important;
#     border-radius: 16px 16px 4px 16px !important;
#     font-size: 16px !important;
# }

# .bot {
#     background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
#     border: 1px solid #e2e8f0;
#     border-radius: 16px 16px 16px 4px !important;
#     font-size: 16px !important;
# }

# .user p, .bot p {
#     font-size: 16px !important;
#     line-height: 1.6 !important;
# }

# .message {
#     font-size: 16px !important;
# }

# #chatbot .message-wrap .message {
#     font-size: 16px !important;
#     line-height: 1.6 !important;
# }

# label {
#     font-weight: 600 !important;
#     color: #1e293b !important;
#     font-size: 14px !important;
# }

# .input-wrap textarea {
#     border: 2px solid #e5e7eb !important;
#     border-radius: 10px !important;
#     padding: 12px !important;
#     font-size: 15px !important;
#     transition: all 0.3s ease !important;
# }

# .input-wrap textarea:focus {
#     border-color: #667eea !important;
#     box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
# }

# .primary {
#     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
#     border: none !important;
#     color: white !important;
#     font-weight: 600 !important;
#     padding: 12px 32px !important;
#     border-radius: 10px !important;
#     transition: all 0.3s ease !important;
#     box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
# }

# .primary:hover {
#     transform: translateY(-2px) !important;
#     box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5) !important;
# }

# button {
#     border-radius: 10px !important;
#     font-weight: 600 !important;
#     transition: all 0.3s ease !important;
# }

# button:not(.primary) {
#     background: #f1f5f9 !important;
#     color: #475569 !important;
#     border: 2px solid #e2e8f0 !important;
# }

# button:not(.primary):hover {
#     background: #e2e8f0 !important;
#     border-color: #cbd5e1 !important;
# }

# footer {
#     display: none !important;
# }

# .wrap {
#     border-radius: 12px !important;
# }

# .settings-button {
#     position: fixed;
#     top: 20px;
#     right: 20px;
#     z-index: 1000;
#     width: 50px;
#     height: 50px;
#     border-radius: 50% !important;
#     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
#     box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
#     display: flex;
#     align-items: center;
#     justify-content: center;
#     cursor: pointer;
#     transition: all 0.3s ease !important;
# }

# .settings-button:hover {
#     transform: scale(1.1) rotate(90deg) !important;
#     box-shadow: 0 6px 16px rgba(102, 126, 234, 0.6) !important;
# }
# """

# # Modern Gradio interface
# with gr.Blocks(css=custom_css, theme=gr.themes.Soft(
#     primary_hue="blue",
#     secondary_hue="purple",
# ), title="🔒 Privacy-Protected Chatbot") as gradio_ui:
    
#     # Settings state
#     settings_visible = gr.State(False)
    
#     gr.HTML("""
#         <div style='text-align: center; padding: 16px; background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); 
#                     border-radius: 10px; margin-top: 20px; border: 1px solid #cbd5e1;'>
#             <div style='display: flex; justify-content: center; gap: 30px; flex-wrap: wrap;'>
#                 <div>
#                     <span style='font-size: 24px;'>🔴</span>
#                     <strong style='color: #dc2626; margin-left: 8px;'>HIGH</strong>
#                     <p style='color: #64748b; font-size: 13px; margin: 4px 0 0 0;'>Aadhaar, PAN, Cards, CVV</p>
#                 </div>
#                 <div>
#                     <span style='font-size: 24px;'>🟡</span>
#                     <strong style='color: #f59e0b; margin-left: 8px;'>MEDIUM</strong>
#                     <p style='color: #64748b; font-size: 13px; margin: 4px 0 0 0;'>Email, Phone, Postal Code</p>
#                 </div>
#                 <div>
#                     <span style='font-size: 24px;'>🟢</span>
#                     <strong style='color: #10b981; margin-left: 8px;'>SAFE</strong>
#                     <p style='color: #64748b; font-size: 13px; margin: 4px 0 0 0;'>No Sensitive Data</p>
#                 </div>
#             </div>
#         </div>
#     """)
    
#     # Event handlers
#     def submit_message(message, history, strict, logging, sensitivity):
#         return "", gradio_chat(message, history, strict, logging, sensitivity)
    
#     def clear_chat():
#         return []
    
#     def toggle_settings(current_state):
#         return not current_state, gr.update(visible=not current_state)
    
#     def save_settings(strict, logging, sensitivity):
#         msg = update_settings(strict, logging, sensitivity)
#         return gr.update(value=msg, visible=True)
    
#     msg.submit(submit_message, [msg, chatbot, strict_privacy, enable_logging, sensitivity_level], [msg, chatbot])
#     send_btn.click(submit_message, [msg, chatbot, strict_privacy, enable_logging, sensitivity_level], [msg, chatbot])
#     clear_btn.click(clear_chat, None, chatbot)
    
#     settings_btn.click(
#         toggle_settings,
#         inputs=[settings_visible],
#         outputs=[settings_visible, settings_panel]
#     )
    
#     save_settings_btn.click(
#         save_settings,
#         inputs=[strict_privacy, enable_logging, sensitivity_level],
#         outputs=[settings_output]
#     )

# # Mount Gradio to FastAPI
# app = gr.mount_gradio_app(app, gradio_ui, path="/gradio")