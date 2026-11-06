
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os
import time
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
client = genai.Client(api_key=API_KEY) if API_KEY else None

SYSTEM_INSTRUCTION = """
You are SARA, a helpful, friendly and accurate AI assistant.
Answer naturally and clearly. Match the user's language.
Use recent conversation history and saved personal memory when relevant.
Never invent personal facts or claim to remember information you do not have.
"""

MEMORY_INSTRUCTION = """
You are SARA's automatic memory manager.

Read the existing memory and recent conversation.

Extract important, long-term facts explicitly shared by the user, such as:
- Name and preferred way of being addressed
- Favourite things and preferences
- Education, skills and interests
- Ongoing projects and career goals
- Stable preferences and recurring requirements

Rules:
1. Save only facts actually stated by the user.
2. Do not save guesses or hypothetical examples.
3. Do not save passwords, API keys or sensitive credentials.
4. Avoid temporary, irrelevant conversation details.
5. Preserve existing useful memories.
6. Update a fact if the user clearly corrects it.
7. Keep the memory concise and organised.
8. Return ONLY the updated memory as plain text.
9. Maximum length: 4500 characters.
"""

def generate_response(contents, config):
    for attempt in range(3):
        try:
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=config
            )
        except Exception as error:
            error_text = str(error)
            retryable = any(code in error_text for code in (
                "503", "UNAVAILABLE", "429",
                "RESOURCE_EXHAUSTED", "500", "INTERNAL"
            ))
            if retryable and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "ai_configured": client is not None
    })

@app.post("/chat")
def chat():
    if client is None:
        return jsonify({
            "reply": "SARA is not configured yet. Check your .env file."
        }), 503

    data = request.get_json(silent=True) or {}

    user_message = data.get("message", "")
    history = data.get("history", [])
    memory = data.get("memory", "")

    if not isinstance(user_message, str):
        return jsonify({"reply": "Please send a valid message."}), 400

    user_message = user_message.strip()

    if not user_message:
        return jsonify({"reply": "Please enter a message."}), 400

    if len(user_message) > 12000:
        return jsonify({"reply": "Your message is too long."}), 413

    if not isinstance(history, list):
        history = []

    if not isinstance(memory, str):
        memory = ""

    memory = memory.strip()[:5000]

    system_instruction = SYSTEM_INSTRUCTION

    if memory:
        system_instruction += (
            "\n\nUSER'S SAVED PERSONAL MEMORY:\n" + memory
        )

    contents = []

    for item in history[-24:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if role in ("user", "model") and isinstance(content, str):
            if content.strip():
                contents.append({
                    "role": role,
                    "parts": [{"text": content[:12000]}]
                })

    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    try:
        # Generate normal AI response
        response = generate_response(
            contents,
            types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=2048
            )
        )

        reply = (response.text or "").strip()

        if not reply:
            return jsonify({
                "reply": "I couldn't generate a response. Please try again."
            }), 502

        # Automatically extract and update long-term memory
        updated_memory = memory

        try:
            recent_conversation = "EXISTING MEMORY:\n"
            recent_conversation += memory or "(No saved memory yet)"
            recent_conversation += "\n\nRECENT CONVERSATION:\n"

            recent_messages = contents[-12:]

            for item in recent_messages:
                role = item.get("role", "user")
                text = " ".join(
                    part.get("text", "")
                    for part in item.get("parts", [])
                )

                recent_conversation += (
                    f"\n{role.upper()}: {text[:2500]}"
                )

            memory_response = generate_response(
                recent_conversation,
                types.GenerateContentConfig(
                    system_instruction=MEMORY_INSTRUCTION,
                    temperature=0.1,
                    max_output_tokens=700
                )
            )

            extracted_memory = (
                memory_response.text or ""
            ).strip()

            if extracted_memory and len(extracted_memory) <= 5000:
                updated_memory = extracted_memory

        except Exception:
            logging.exception(
                "Memory extraction failed. Normal chat will continue."
            )

        return jsonify({
            "reply": reply,
            "updated_memory": updated_memory
        })

    except Exception as exc:
        error_text = str(exc)
        logging.exception("Gemini request failed")

        if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
            message = "AI usage limit reached. Please try again later."
            status = 429

        elif "503" in error_text or "UNAVAILABLE" in error_text:
            message = "AI service is temporarily busy. Try again shortly."
            status = 503

        elif "404" in error_text or "NOT_FOUND" in error_text:
            message = f"Gemini model {MODEL_NAME} is unavailable."
            status = 502

        elif "401" in error_text or "403" in error_text:
            message = "Gemini API key was rejected. Check your .env file."
            status = 502

        else:
            message = "Something went wrong. Please try again."
            status = 502

        return jsonify({
            "reply": message,
            "error": "ai_service"
        }), status

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        debug=True
    )
