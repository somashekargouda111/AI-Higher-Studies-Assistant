"""Communication with Google Gemini through the OpenAI-compatible API."""

import json
import time

from openai import (
    OpenAI,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
)

from .config import MODEL, MAX_HISTORY
from .prompts import SYSTEM_PROMPT
from .profile import profile_to_text


class ChatError(Exception):
    """Friendly error that can be shown to the student."""


class LLMClient:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=60,
        )
        self.model = MODEL

    def _call(self, **kwargs):
        """Call Gemini with retries for temporary errors."""

        max_retries = 3

        for attempt in range(max_retries):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    **kwargs,
                )

            except AuthenticationError:
                raise ChatError(
                    "🔑 Your Google AI Studio API key is invalid. "
                    "Please check your API key."
                )

            except RateLimitError:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue

                raise ChatError(
                    "⏳ Gemini API rate limit or quota reached. "
                    "Please wait and try again."
                )

            except APIStatusError as e:
                if e.status_code == 503:
                    if attempt < max_retries - 1:
                        time.sleep(5)
                        continue

                    raise ChatError(
                        "⚠️ Gemini is temporarily busy. "
                        "Please wait and try again."
                    )

                raise ChatError(
                    f"⚠️ Gemini returned an error "
                    f"(status {e.status_code})."
                )

            except APITimeoutError:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue

                raise ChatError(
                    "⌛ The request timed out. Please try again."
                )

            except APIConnectionError:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue

                raise ChatError(
                    "🌐 Could not connect to Google Gemini. "
                    "Please check your internet connection."
                )

            except Exception as e:
                raise ChatError(
                    f"⚠️ Something unexpected happened: {e}"
                )

        raise ChatError(
            "⚠️ Gemini is temporarily unavailable."
        )

    def generate_reply_and_profile(self, history, profile):
        """
        Make ONE Gemini API call.

        Gemini gives the student a normal natural-language answer.
        Profile information is optionally extracted from a JSON block.
        """

        profile_context = profile_to_text(profile)

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "system",
                "content": (
                    "CURRENT STUDENT PROFILE:\n"
                    + profile_context
                    + "\n\n"
                    "Use this profile as context when answering. "
                    "Only update profile information when the student "
                    "explicitly provides it."
                ),
            },
        ]

        messages.extend(history[-MAX_HISTORY:])

        # Ask for a normal answer plus a small profile section.
        messages.append(
            {
                "role": "system",
                "content": """
At the end of your response, add this exact marker:

===PROFILE_DATA===

After the marker, provide ONLY a JSON object containing
student information that was explicitly provided by the student.

The JSON object should use these fields:

{
  "name": "",
  "degree": "",
  "branch": "",
  "year_or_semester": "",
  "cgpa_or_percentage": "",
  "graduation_year": "",
  "subjects": [],
  "skills": [],
  "interests": [],
  "career_goal": "",
  "industry_preference": "",
  "research_or_industry": "",
  "location_preference": "",
  "preferred_country": "",
  "budget": "",
  "study_mode": "",
  "duration": ""
}

Do not invent information.

If no new profile information is available, return:

{}

The normal answer before ===PROFILE_DATA=== should be
helpful, natural and easy for a student to understand.
""",
            }
        )

        # ONE Gemini API call
        response = self._call(
            messages=messages,
            temperature=0.5,
        )

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError):
            raise ChatError(
                "⚠️ Could not read Gemini's response."
            )

        if not content:
            raise ChatError(
                "⚠️ Gemini returned an empty response."
            )

        content = content.strip()

        marker = "===PROFILE_DATA==="

        # ---------------------------------------------------------
        # Extract answer and profile
        # ---------------------------------------------------------

        if marker in content:

            reply_part, profile_part = content.split(
                marker,
                1,
            )

            reply = reply_part.strip()
            profile_part = profile_part.strip()

            # Remove Markdown code fences if Gemini adds them.
            if profile_part.startswith("```"):
                profile_part = profile_part.replace(
                    "```json",
                    "",
                    1,
                )
                profile_part = profile_part.replace(
                    "```",
                    "",
                )
                profile_part = profile_part.strip()

            try:
                extracted_profile = json.loads(profile_part)

                if not isinstance(extracted_profile, dict):
                    extracted_profile = {}

            except json.JSONDecodeError:
                # The AI answer is still usable.
                extracted_profile = {}

        else:
            # If Gemini doesn't provide the profile marker,
            # keep the normal AI response.
            reply = content
            extracted_profile = {}

        if not reply:
            raise ChatError(
                "⚠️ Gemini did not provide a valid answer."
            )

        return reply, extracted_profile