"""AI Higher Studies Assistant - Streamlit UI.
Run with: streamlit run app.py
"""

import streamlit as st

from core.config import get_api_key
from core.llm_client import LLMClient, ChatError
from core.profile import new_profile, merge_profile, FIELDS, SECTIONS
from core.prompts import QUICK_ACTIONS


st.set_page_config(
    page_title="AI Higher Studies Assistant",
    page_icon="🎓",
    layout="wide",
)


WELCOME = (
    "Hi! 👋 I'm your Higher Studies Assistant. "
    "I can help you explore postgraduate paths that fit "
    "your background and goals.\n\n"
    "To start, tell me a bit about yourself — for example, "
    "**your degree, branch and current year**."
)


# ---------- Session state ----------
def init_state():

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": WELCOME,
                "display": WELCOME,
            }
        ]

    if "profile" not in st.session_state:
        st.session_state.profile = new_profile()

    if "pending" not in st.session_state:
        st.session_state.pending = None


# ---------- Conversation manager ----------
def handle_message(client, display_text, prompt_text):
    """
    Process one student message using ONE Gemini API call.

    The same API response provides:
    - personalized chatbot reply
    - updated student profile
    """

    if not prompt_text or not prompt_text.strip():
        st.warning("Please type a message first.")
        return

    user_message = prompt_text.strip()

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
            "display": display_text.strip(),
        }
    )

    history = [
        {
            "role": m["role"],
            "content": m["content"],
        }
        for m in st.session_state.messages
    ]

    try:
        # ONE Gemini API call only
        reply, extracted_profile = client.generate_reply_and_profile(
            history,
            st.session_state.profile,
        )

        # Update the student profile using information
        # extracted from the same Gemini response.
        if extracted_profile:
            merge_profile(
                st.session_state.profile,
                extracted_profile,
            )

    except ChatError as e:

        # Remove failed user message so the student
        # can try again.
        st.session_state.messages.pop()

        st.error(str(e))
        return

    # Add AI response to conversation
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply,
            "display": reply,
        }
    )


# ---------- Sidebar ----------
def render_sidebar():

    with st.sidebar:

        st.header("👤 Student Profile")

        profile = st.session_state.profile

        if not any(profile.values()):
            st.caption(
                "Your profile will fill in as we chat."
            )

        for section, keys in SECTIONS.items():

            st.subheader(section)

            shown = False

            for k in keys:

                label, is_list = FIELDS[k]
                value = profile[k]

                if value:

                    if is_list:
                        shown_value = ", ".join(value)
                    else:
                        shown_value = value

                    st.markdown(
                        f"**{label}:** {shown_value}"
                    )

                    shown = True

            if not shown:
                st.caption("— not shared yet —")

        st.divider()

        st.subheader("⚡ Quick Actions")

        for label, prompt in QUICK_ACTIONS.items():

            if st.button(
                label,
                use_container_width=True,
            ):

                st.session_state.pending = (
                    label,
                    prompt,
                )

                st.rerun()

        st.divider()

        if st.button(
            "🔄 Start New Conversation",
            use_container_width=True,
        ):

            for key in (
                "messages",
                "profile",
                "pending",
            ):
                st.session_state.pop(key, None)

            st.rerun()

        st.caption(
            "Educational guidance only. Always verify "
            "university requirements, fees and deadlines "
            "on official websites."
        )


# ---------- Main ----------
def main():

    init_state()

    st.title(
        "🎓 AI Higher Studies Assistant"
    )

    st.caption(
        "Explore postgraduate study pathways based on "
        "your academic background and career interests."
    )

    api_key = get_api_key()

    if not api_key:

        st.error(
            "GEMINI_API_KEY not found. "
            "Check your `.env` file and restart the application."
        )

        st.stop()

    client = LLMClient(api_key)

    # Handle typed message
    typed = st.chat_input(
        "Tell me about your degree, interests or goals..."
    )

    if typed is not None:

        if not typed.strip():

            st.warning(
                "Please type a message first."
            )

        else:

            with st.spinner("Thinking..."):

                handle_message(
                    client,
                    typed,
                    typed,
                )

    # Handle quick action
    elif st.session_state.pending:

        label, prompt = (
            st.session_state.pending
        )

        st.session_state.pending = None

        with st.spinner(
            "Analysing your profile..."
        ):

            handle_message(
                client,
                label,
                prompt,
            )

    # Sidebar
    render_sidebar()

    # Chat history
    for message in st.session_state.messages:

        with st.chat_message(
            message["role"],
            avatar=(
                "🎓"
                if message["role"] == "assistant"
                else "🧑‍🎓"
            ),
        ):

            st.markdown(
                message["display"]
            )


main()