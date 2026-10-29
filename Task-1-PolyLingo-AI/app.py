import streamlit as st
import requests
import re
from langdetect import detect, LangDetectException
import speech_recognition as sr
from hashlib import md5
from gtts import gTTS
from io import BytesIO

st.set_page_config(page_title="PolyLingo AI", page_icon="🌍", layout="wide")

st.markdown("""
<style>
/* PolyLingo AI: explicit, high-contrast styling for both Streamlit themes. */
:root {
  --pl-bg: #f4f7fb;
  --pl-panel: #ffffff;
  --pl-text: #172033;
  --pl-muted: #43516a;
  --pl-border: #b8c5d8;
  --pl-input: #ffffff;
  --pl-input-text: #172033;
  --pl-accent: #155eef;
  --pl-select-bg: #ffffff;
  --pl-select-text: #172033;
}
html[data-theme="light"], body[data-theme="light"], [data-theme="light"] {
  color-scheme: light;
  --pl-bg: #f4f7fb;
  --pl-panel: #ffffff;
  --pl-text: #172033;
  --pl-muted: #43516a;
  --pl-border: #b8c5d8;
  --pl-input: #ffffff;
  --pl-input-text: #172033;
  --pl-accent: #155eef;
  --pl-select-bg: #ffffff;
  --pl-select-text: #172033;
}
html[data-theme="dark"], body[data-theme="dark"], [data-theme="dark"] {
  color-scheme: dark;
  --pl-bg: #101426;
  --pl-panel: #18213a;
  --pl-text: #f4f7ff;
  --pl-muted: #c5d0e8;
  --pl-border: #536486;
  --pl-input: #151d32;
  --pl-input-text: #f4f7ff;
  --pl-accent: #245fe8;
  --pl-select-bg: #151d32;
  --pl-select-text: #f4f7ff;
}
.stApp, [data-testid="stAppViewContainer"] {
  background: var(--pl-bg) !important;
  color: var(--pl-text) !important;
}
.stApp p, .stApp label, .stApp li, .stApp span,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp small,
[data-testid="stSidebar"] *, [data-testid="stTabs"] button {
  color: var(--pl-text);
}
[data-testid="stSidebar"] {
  background: var(--pl-panel) !important;
  border-right: 1px solid var(--pl-border) !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] .stCaption,
[data-testid="stCaptionContainer"] {
  color: var(--pl-muted) !important;
}
.hero {
  text-align: center;
  padding: 25px 10px 18px;
  background: linear-gradient(120deg, #173b70, #075bd8 55%, #233c88);
  border: 1px solid #5269a2;
  border-radius: 18px;
  margin-bottom: 20px;
}
.hero h1 { font-size: clamp(30px, 4vw, 46px); font-weight: 800; color: #ffffff !important; margin-bottom: 5px; }
.hero p { color: #ffffff !important; font-size: 16px; }
div.stButton > button, [data-testid="stDownloadButton"] button {
  border-radius: 10px !important;
  border: 1px solid var(--pl-accent) !important;
  background: var(--pl-accent) !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  min-height: 43px;
  width: 100%;
}
div.stButton > button p, [data-testid="stDownloadButton"] button p,
div.stButton > button span, [data-testid="stDownloadButton"] button span {
  color: #ffffff !important;
}
div.stButton > button:hover, [data-testid="stDownloadButton"] button:hover {
  border-color: var(--pl-text) !important;
  filter: brightness(1.08);
}
textarea, input, [data-baseweb="select"] > div { border-radius: 10px !important; }
[data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input {
  background: var(--pl-input) !important;
  color: var(--pl-input-text) !important;
  border: 1px solid var(--pl-border) !important;
  -webkit-text-fill-color: var(--pl-input-text) !important;
}
/* Fix the dark dropdowns that remained visible in light mode. */
[data-baseweb="select"] > div,
[data-baseweb="select"] div[role="combobox"],
[data-baseweb="select"] div[class*="control"] {
  background: var(--pl-select-bg) !important;
  color: var(--pl-select-text) !important;
  border-color: var(--pl-border) !important;
}
[data-baseweb="select"] input,
[data-baseweb="select"] div,
[data-baseweb="select"] span {
  color: var(--pl-select-text) !important;
  -webkit-text-fill-color: var(--pl-select-text) !important;
}
[data-baseweb="popover"], [data-baseweb="menu"],
[role="listbox"], [role="option"] {
  background: var(--pl-panel) !important;
  color: var(--pl-text) !important;
}
[role="option"]:hover { background: var(--pl-border) !important; }
/* Improve labels, captions, tabs, and the voice recorder area. */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label,
[data-testid="stMarkdownContainer"] p, .stCaption,
[data-testid="stTabs"] button p {
  color: var(--pl-text) !important;
}
[data-testid="stAudioInput"] button {
  color: var(--pl-text) !important;
  background: var(--pl-panel) !important;
  border: 1px solid var(--pl-border) !important;
}
[data-testid="stTabs"] button { color: var(--pl-text) !important; }
[data-testid="stExpander"] {
  background: var(--pl-panel) !important;
  border: 1px solid var(--pl-border) !important;
  border-radius: 10px !important;
}
[data-testid="stAlert"] p { color: inherit !important; }
</style>
<div class="hero">
  <h1>🌍 PolyLingo AI</h1>
  <p>Break language barriers with intelligent translation.</p>
</div>
""", unsafe_allow_html=True)

LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Punjabi": "pa",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese (Simplified)": "zh-CN",
    "Arabic": "ar",
    "Portuguese": "pt",
    "Russian": "ru",
    "Bengali": "bn",
    "Urdu": "ur",
    "Tamil": "ta",
    "Telugu": "te",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Nepali": "ne"
}

SPEECH_LANGUAGES = {
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Punjabi": "pa-IN",
    "French": "fr-FR",
    "Spanish": "es-ES",
    "German": "de-DE",
    "Italian": "it-IT",
    "Japanese": "ja-JP",
    "Korean": "ko-KR",
    "Chinese (Simplified)": "zh-CN",
    "Arabic": "ar-SA",
    "Portuguese": "pt-PT",
    "Russian": "ru-RU",
    "Bengali": "bn-IN",
    "Urdu": "ur-PK",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Marathi": "mr-IN",
    "Gujarati": "gu-IN",
    "Nepali": "ne-NP"
}

if "history" not in st.session_state:
    st.session_state.history = []
if "translated_text" not in st.session_state:
    st.session_state.translated_text = ""
if "source_text" not in st.session_state:
    st.session_state.source_text = ""
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None


def clear_translation():
    st.session_state.input_text = ""
    st.session_state.translated_text = ""
    st.session_state.source_text = ""
    st.session_state.audio_data = None
    st.session_state.pop("last_audio_hash", None)


def transliterate_hinglish(text):
    response = requests.get(
        "https://inputtools.google.com/request",
        params={
            "text": text,
            "itc": "hi-t-i0-und",
            "num": 5,
            "cp": 0,
            "cs": 1,
            "ie": "utf-8",
            "oe": "utf-8"
        },
        timeout=10
    )
    response.raise_for_status()
    payload = response.json()
    if payload and payload[0] == "SUCCESS":
        candidates = payload[1][0][1]
        if candidates:
            return candidates[0]
    return text


@st.cache_data(show_spinner=False, ttl=1800)
def translate_text(source_text, source_language, target_language):
    original_text = source_text.strip()
    if not original_text:
        raise ValueError("Please enter some text to translate.")

    target_code = LANGUAGES[target_language]
    hinglish_words = {
        "hai", "hain", "hun", "hoon", "ho", "aaj", "bahut", "khush",
        "mera", "meri", "main", "mujhe", "tum", "kaise", "kya", "nahi",
        "nahin", "acha", "achha", "karna", "karo", "chahiye", "kyunki",
        "accha", "acchi", "theek", "thik", "yaar", "bhai", "kyun",
        "tera", "tere", "apna", "apni", "ham", "hum", "raha", "rahi",
        "rahe", "aap", "ka", "ki", "ke", "mein", "mere", "teri", "kuch",
        "abhi", "kahan", "kab", "kyunki", "hoon"
    }
    words = set(re.findall(r"[a-zA-Z]+", original_text.lower()))
    is_hinglish = bool(words.intersection(hinglish_words))
    has_devanagari = bool(re.search(r"[\u0900-\u097F]", original_text))

    if source_language == "Auto Detect":
        if has_devanagari or is_hinglish:
            source_code = "hi"
        else:
            try:
                detected_code = detect(original_text)
                source_code = detected_code if detected_code in set(LANGUAGES.values()) else "en"
            except LangDetectException:
                source_code = "en"
    else:
        source_code = LANGUAGES[source_language]

    text_to_translate = original_text

    if source_code == "hi" and is_hinglish and not has_devanagari:
        try:
            text_to_translate = transliterate_hinglish(original_text)
        except (requests.RequestException, ValueError, IndexError, TypeError):
         
            text_to_translate = original_text

    if source_code.lower() == target_code.lower():
        return text_to_translate

    response = requests.get(
        "https://translate.googleapis.com/translate_a/single",
        params={
            "client": "gtx",
            "sl": source_code,
            "tl": target_code,
            "dt": "t",
            "q": text_to_translate
        },
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )
    response.raise_for_status()
    payload = response.json()

    if not payload or not payload[0]:
        raise RuntimeError("The translation service returned an empty result.")

    translated = "".join(
        part[0] for part in payload[0]
        if isinstance(part, list) and part and part[0]
    ).strip()

    if not translated:
        raise RuntimeError("The translation service returned an empty result.")

    if translated.casefold() == text_to_translate.casefold() and source_code != target_code:
        raise RuntimeError(
            "The free translation service returned the same text instead of translating it. "
            "This can happen when the service is busy or the source language was detected incorrectly. "
            "Try choosing the source language manually or retry later."
        )

    return translated


with st.sidebar:
    st.title("⚙️ Settings")
    app_theme = st.radio("App appearance", ["Dark", "Light"], index=0, horizontal=True, key="app_theme")
    st.markdown("### About PolyLingo AI")
    st.write("Your personal multilingual translation workspace.")
    st.markdown("---")
    st.markdown("**Features**")
    st.write("🌐 Translation across 20 languages")
    st.write("🎙️ Voice input")
    st.write("📚 Recent translation history")
    st.write("🔊 Spoken translation output")
    st.write("⬇️ Downloadable results")
    st.markdown("---")
    st.caption("Free online services are used. Internet is required; rate limits may apply.")

# Explicit in-app theme: this does not depend on Streamlit's browser theme setting.
if app_theme == "Dark":
    theme_css = """
    <style>
    :root { color-scheme: dark; --pl-bg:#0b1220; --pl-panel:#111c31; --pl-text:#f4f7ff; --pl-muted:#c4cee0; --pl-border:#3b4c6b; --pl-input:#16233b; --pl-input-text:#f4f7ff; --pl-accent:#1769e8; --pl-select-bg:#16233b; --pl-select-text:#f4f7ff; }
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] { background:var(--pl-bg) !important; color:var(--pl-text) !important; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div { background:var(--pl-panel) !important; color:var(--pl-text) !important; }
    .stApp p, .stApp label, .stApp li, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp small, [data-testid="stWidgetLabel"] *, [data-testid="stMarkdownContainer"] *, [data-testid="stTabs"] button { color:var(--pl-text) !important; }
    [data-testid="stCaptionContainer"], [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:var(--pl-muted) !important; }
    [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input, [data-baseweb="select"] > div, [data-testid="stAudioInput"] button { background:var(--pl-input) !important; color:var(--pl-input-text) !important; -webkit-text-fill-color:var(--pl-input-text) !important; border-color:var(--pl-border) !important; }
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [role="option"] { background:var(--pl-panel) !important; color:var(--pl-text) !important; }
    header[data-testid="stHeader"] { background:var(--pl-bg) !important; }
    header[data-testid="stHeader"] *, [data-testid="stToolbar"] *, [data-testid="stDecoration"] { color:var(--pl-text) !important; }
    [data-testid="stToolbar"] { background:var(--pl-bg) !important; }
    </style>
    """
else:
    theme_css = """
    <style>
    :root { color-scheme:light; --pl-bg:#f4f7fb; --pl-panel:#ffffff; --pl-text:#172033; --pl-muted:#43516a; --pl-border:#b8c5d8; --pl-input:#ffffff; --pl-input-text:#172033; --pl-accent:#155eef; --pl-select-bg:#ffffff; --pl-select-text:#172033; }
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] { background:var(--pl-bg) !important; color:var(--pl-text) !important; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div { background:var(--pl-panel) !important; color:var(--pl-text) !important; }
    .stApp p, .stApp label, .stApp li, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp small, [data-testid="stWidgetLabel"] *, [data-testid="stMarkdownContainer"] *, [data-testid="stTabs"] button { color:var(--pl-text) !important; }
    [data-testid="stCaptionContainer"], [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:var(--pl-muted) !important; }
    [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input, [data-baseweb="select"] > div, [data-testid="stAudioInput"] button { background:var(--pl-input) !important; color:var(--pl-input-text) !important; -webkit-text-fill-color:var(--pl-input-text) !important; border-color:var(--pl-border) !important; }
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [role="option"] { background:var(--pl-panel) !important; color:var(--pl-text) !important; }
    header[data-testid="stHeader"] { background:var(--pl-bg) !important; }
    header[data-testid="stHeader"] *, [data-testid="stToolbar"] *, [data-testid="stDecoration"] { color:var(--pl-text) !important; }
    [data-testid="stToolbar"] { background:var(--pl-bg) !important; }
    </style>
    """
st.markdown(theme_css, unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🌐 Translator", "📚 History", "ℹ️ About"])

with tab1:
    st.markdown("### Translate anything")
    col1, col2 = st.columns(2)

    with col1:
        source_language = st.selectbox(
            "Translate from",
            ["Auto Detect"] + list(LANGUAGES.keys())
        )
    with col2:
        target_language = st.selectbox(
            "Translate to",
            list(LANGUAGES.keys()),
            index=1
        )

    audio_value = st.audio_input("🎙️ Record your voice")

    if audio_value:
        audio_bytes = audio_value.getvalue()
        audio_hash = md5(audio_bytes).hexdigest()

        if st.session_state.get("last_audio_hash") != audio_hash:
            try:
                recognizer = sr.Recognizer()
                with sr.AudioFile(BytesIO(audio_bytes)) as source:
                    audio = recognizer.record(source)

                # Speech recognition needs a language hint. Auto Detect
                # defaults to English; select Hindi/Punjabi before recording
                # if speaking those languages.
                speech_language = SPEECH_LANGUAGES.get(source_language, "en-IN")

                with st.spinner("Converting speech to text..."):
                    recognized_text = recognizer.recognize_google(
                        audio,
                        language=speech_language
                    )

                st.session_state.input_text = recognized_text
                st.session_state.last_audio_hash = audio_hash
                st.success("Voice converted to text successfully!")
                st.rerun()

            except sr.UnknownValueError:
                st.warning("Sorry, speech samajh nahi aayi. Please speak clearly.")
            except sr.RequestError:
                st.error("Speech recognition service unavailable. Check your internet.")
            except Exception as error:
                st.error("Voice input failed.")
                with st.expander("Technical Details"):
                    st.code(str(error))

    text_input = st.text_area(
        "Enter your text",
        placeholder="Type, paste, or record your voice...",
        height=190,
        max_chars=5000,
        key="input_text"
    )
    st.caption(f"Characters: {len(text_input)} / 5000")

    col1, col2 = st.columns([2, 1])
    with col1:
        translate_clicked = st.button("✨ Translate Now", use_container_width=True)
    with col2:
        st.button("🗑️ Clear", use_container_width=True, on_click=clear_translation)

    if translate_clicked:
        st.session_state.translated_text = ""
        st.session_state.audio_data = None

        if not text_input.strip():
            st.warning("Please enter some text first.")
        elif source_language != "Auto Detect" and source_language == target_language:
            st.warning("Choose two different languages.")
        else:
            try:
                with st.spinner("Translating your text..."):
                    result = translate_text(
                        text_input.strip(),
                        source_language,
                        target_language
                    )

                if result:
                    st.session_state.translated_text = result
                    st.session_state.source_text = text_input.strip()
                    st.session_state.history.insert(0, {
                        "source": text_input.strip(),
                        "translation": result,
                        "source_language": source_language,
                        "target_language": target_language
                    })
                    st.success("Translation completed!")
                else:
                    st.warning("No translation was returned.")

            except requests.Timeout:
                st.error("Translation service took too long. Please try again.")
            except requests.HTTPError as error:
                if error.response is not None and error.response.status_code == 429:
                    st.warning(
                        "The free translation service is limiting requests right now. "
                        "Please try again later."
                    )
                else:
                    st.error("Translation service returned an error. Please try again.")
                with st.expander("Technical Details"):
                    st.code(str(error))
            except requests.RequestException as error:
                st.error("Could not connect to the translation service. Check your internet.")
                with st.expander("Technical Details"):
                    st.code(str(error))
            except Exception as error:
                st.error("Translation failed. Please try another source language or try again.")
                with st.expander("Technical Details"):
                    st.code(str(error))

    if st.session_state.translated_text:
        st.markdown("---")
        st.markdown("### 📝 Translated Result")
        st.text_area(
            "Your translation",
            value=st.session_state.translated_text,
            height=180,
            disabled=True
        )
        st.download_button(
            "⬇️ Download Translation",
            data=st.session_state.translated_text,
            file_name="polylingo_translation.txt",
            mime="text/plain",
            use_container_width=True
        )

        if st.button("🔊 Listen to Translation"):
            try:
                with st.spinner("Generating audio..."):
                    audio_buffer = BytesIO()
                    tts = gTTS(
                        text=st.session_state.translated_text,
                        lang=LANGUAGES[target_language]
                    )
                    tts.write_to_fp(audio_buffer)
                    st.session_state.audio_data = audio_buffer.getvalue()
            except Exception as error:
                st.error(
                    "Audio generation failed. This language may not be supported "
                    "by the text-to-speech service."
                )
                with st.expander("Technical Details"):
                    st.code(str(error))

        if st.session_state.audio_data:
            st.audio(st.session_state.audio_data, format="audio/mp3")

with tab2:
    st.markdown("### 📚 Recent Translations")
    if not st.session_state.history:
        st.info("Your translation history will appear here.")
    else:
        if st.button("🧹 Clear History"):
            st.session_state.history = []
            st.rerun()

        for index, item in enumerate(st.session_state.history, start=1):
            with st.expander(
                f"{index}. {item['source_language']} → {item['target_language']}"
            ):
                st.markdown("**Original Text**")
                st.write(item["source"])
                st.markdown("**Translated Text**")
                st.write(item["translation"])

with tab3:
    st.markdown("### About this project")
    st.write(
        "PolyLingo AI is a multilingual translation application built with "
        "Python and Streamlit."
    )
    st.markdown("#### Features")
    st.write("- Multilingual text translation")
    st.write("- Automatic source-language detection")
    st.write("- Voice input with selectable speech language")
    st.write("- Translation history during the current session")
    st.write("- Downloadable translation results")
    st.write("- Text-to-speech audio playback")
    st.write("- Translation error handling")
    st.write("- Clear input and translation options")
    st.markdown("---")
    st.caption(
        "Translations require an internet connection. Free translation services "
        "may have usage limits, and quality may vary by language and context."
    )
