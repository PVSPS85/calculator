"""Google GenAI Gemini service integration for CalcAI.

Manages conversational sessions, prompt engineering, system instructions,
and upstream error handling using the official Google GenAI SDK.
"""

import uuid
from typing import Dict, List, Optional, Tuple, Any
from google import genai
from google.genai import types
from google.genai.errors import APIError

from backend.app.core.config import settings


class GeminiServiceException(Exception):
    """Base exception for Gemini service issues."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class APIKeyNotConfiguredError(GeminiServiceException):
    """Raised when GEMINI_API_KEY is missing or invalid."""
    def __init__(self):
        super().__init__(
            message=(
                "Gemini API key is not configured on the backend. "
                "Please configure your GEMINI_API_KEY in backend/.env "
                "(obtain a free key from https://aistudio.google.com/)."
            ),
            status_code=503,
        )


class GeminiService:
    """Manages chat sessions and interactions with Google Gemini models."""

    SYSTEM_INSTRUCTION = (
        "You are CalcAI, an intelligent mathematical and general assistant embedded "
        "inside a mobile calculator application. Your goals:\n"
        "1. Provide step-by-step mathematical explanations, formula breakdowns, and problem solving.\n"
        "2. Answer general questions accurately, concisely, and helpfully.\n"
        "3. When explaining calculation results, explain the order of operations (PEMDAS/BODMAS) "
        "and the logic behind the solution.\n"
        "4. Keep responses structured, easy to read on mobile screens, and avoid unnecessary jargon."
    )

    def __init__(self):
        self._client: Optional[genai.Client] = None
        # In-memory session store mapping session_id -> list of Content objects
        self._sessions: Dict[str, List[types.Content]] = {}

    def _get_client(self) -> genai.Client:
        """Lazily initialize and return the GenAI client."""
        if not settings.is_api_key_valid:
            raise APIKeyNotConfiguredError()

        if self._client is None:
            self._client = genai.Client(api_key=settings.gemini_api_key.strip())
        return self._client

    def send_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str, str]:
        """Send a message to Gemini maintaining session conversation history.

        Returns:
            Tuple of (response_text, session_id, model_name)
        """
        client = self._get_client()

        # Generate or validate session ID
        active_session_id = session_id if (session_id and session_id.strip()) else str(uuid.uuid4())
        if active_session_id not in self._sessions:
            self._sessions[active_session_id] = []

        history = self._sessions[active_session_id]

        # Construct prompt text with optional calculator context
        prompt_text = message.strip()
        if context and context.get("type") == "explain_calculation":
            expr = context.get("expression", "")
            res = context.get("result", "")
            prompt_text = (
                f"[Calculator Context: Expression='{expr}', Result='{res}']\n\n"
                f"{prompt_text}"
            )

        # Build new user content item
        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)],
        )

        # Prepare payload contents: conversation history + new user prompt
        contents = history + [user_content]

        config = types.GenerateContentConfig(
            system_instruction=self.SYSTEM_INSTRUCTION,
            temperature=0.7,
            max_output_tokens=1500,
        )

        try:
            response = client.models.generate_content(
                model=settings.active_model,
                contents=contents,
                config=config,
            )

            response_text = response.text or "I could not formulate a response for that prompt."

            # Update session history with user message and model reply
            model_content = types.Content(
                role="model",
                parts=[types.Part.from_text(text=response_text)],
            )
            history.append(user_content)
            history.append(model_content)

            # Enforce max history window for MVP memory management
            if len(history) > (settings.max_history_turns * 2):
                self._sessions[active_session_id] = history[-(settings.max_history_turns * 2):]

            return response_text, active_session_id, settings.active_model

        except APIError as e:
            err_msg = str(e).lower()
            if "quota" in err_msg or "rate" in err_msg or e.code == 429:
                raise GeminiServiceException(
                    "Gemini API rate limit or quota exceeded. Please wait a moment before trying again.",
                    status_code=429,
                )
            if "api key" in err_msg or e.code in (400, 401, 403):
                raise GeminiServiceException(
                    "Invalid Gemini API key. Please check your GEMINI_API_KEY in backend/.env.",
                    status_code=401,
                )
            raise GeminiServiceException(
                f"Google Gemini upstream error ({e.code or 'unknown'}): {e.message or 'Request failed'}",
                status_code=502,
            )
        except Exception as e:
            raise GeminiServiceException(
                f"Failed to communicate with AI model: {str(e)}",
                status_code=500,
            )


# Global service instance
gemini_service = GeminiService()
