import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

MAX_HISTORY = 20


def get_api_key():
    """Load the Google Gemini API key."""

    key = os.getenv("GEMINI_API_KEY")

    if key:
        return key.strip()

    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None