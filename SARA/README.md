# SARA – AI Assistant

## Features
- Gemini-powered chat with recent conversation context.
- Browser-local chat history, new chat, reopen, delete and clear.
- Copy replies, timestamps, retry after errors, and suggested prompts.
- Responsive desktop and mobile layout.
- Personal Memory editor: add, edit, or clear saved facts.
- Explicit `Remember that ...` messages can save a fact to browser memory.
- Backend request validation and transient Gemini API retries.

## Setup
1. Install Python 3.10+.
2. Create and activate a virtual environment:
   `python -m venv venv`
3. Install packages:
   `pip install -r requirements.txt`
4. Create `.env` beside `app.py`:
   `GEMINI_API_KEY=YOUR_PRIVATE_KEY`
   `GEMINI_MODEL=gemini-3.5-flash-lite`
5. Run `python app.py` and open http://127.0.0.1:5000.

Keep `.env` private and never upload it to GitHub.

## Personal Memory
Use the **Memory** button in the toolbar to add, edit, or clear facts. You can also send a message starting with `Remember that ...`. Saved memory is stored in this browser's localStorage and included in future chat requests. It does not sync across browsers/devices and is not permanent human-like learning. Do not save passwords, API keys, or sensitive account details.

## Deployment
Set `GEMINI_API_KEY` and optionally `GEMINI_MODEL` as environment variables on your host. Do not commit `.env`. For a Gunicorn deployment run `gunicorn app:app`. Use HTTPS and the hosting provider's secret manager.
