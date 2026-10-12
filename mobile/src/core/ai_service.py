"""AI Assistant client connecting to CalcAI FastAPI Backend.

Replaces mock responses with live HTTP communication to the backend service.
Performs non-blocking requests in background threads to ensure the mobile UI
remains responsive at 60 FPS, with full handling of loading, failure, and retry states.
"""

from typing import Callable, Optional, Dict, Any
import threading
import httpx


class AIService:
    """Manages asynchronous communication with the CalcAI FastAPI backend."""

    def __init__(self, backend_url: str = "http://127.0.0.1:8000"):
        self.session_id: Optional[str] = None
        self.timeout = 30.0
        self.set_backend_url(backend_url)

    def set_backend_url(self, url: str) -> None:
        """Update backend URL (e.g., from Settings dialog), resolving macOS localhost IPv6 timeouts."""
        cleaned = url.rstrip("/")
        if "://localhost" in cleaned:
            cleaned = cleaned.replace("://localhost", "://127.0.0.1")
        self.backend_url = cleaned

    def check_health(self) -> Dict[str, Any]:
        """Synchronously check backend health status."""
        url = f"{self.backend_url}/api/health"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                return {
                    "status": "error",
                    "detail": f"HTTP {resp.status_code}: {resp.text}",
                }
        except Exception as e:
            return {
                "status": "unreachable",
                "detail": str(e),
            }

    def check_health_async(
        self,
        on_result: Callable[[Dict[str, Any]], None],
    ) -> None:
        """Check backend health asynchronously in background thread."""
        def _worker():
            res = self.check_health()
            on_result(res)

        threading.Thread(target=_worker, daemon=True).start()

    def query(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        on_success: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Query the backend AI service asynchronously.

        Args:
            prompt: User message text.
            context: Optional calculation expression & result metadata.
            on_success: Callback function receiving response text.
            on_error: Callback function receiving user-friendly error message.
        """
        def _worker():
            endpoint = f"{self.backend_url}/api/chat"
            payload = {
                "message": prompt,
                "session_id": self.session_id,
                "context": context,
            }

            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(endpoint, json=payload)

                    if resp.status_code == 200:
                        data = resp.json()
                        reply = data.get("reply", "No response received from AI.")
                        self.session_id = data.get("session_id", self.session_id)
                        if on_success:
                            on_success(reply)
                    else:
                        try:
                            err_data = resp.json()
                            detail = err_data.get("detail", resp.text)
                        except Exception:
                            detail = resp.text

                        err_msg = f"Backend error ({resp.status_code}): {detail}"
                        if on_error:
                            on_error(err_msg)

            except httpx.ConnectError:
                err_msg = (
                    f"Unable to connect to CalcAI backend at {self.backend_url}.\n"
                    "• Ensure the backend server is running (e.g. uvicorn backend.app.main:app).\n"
                    "• Configure the correct URL in ⚙ Settings if using an IP or remote host."
                )
                if on_error:
                    on_error(err_msg)

            except httpx.TimeoutException:
                err_msg = (
                    f"Connection timed out waiting for AI response from {self.backend_url}. "
                    "The upstream Gemini API may be experiencing high latency. Please retry."
                )
                if on_error:
                    on_error(err_msg)

            except Exception as e:
                err_msg = f"Network error communicating with AI backend: {str(e)}"
                if on_error:
                    on_error(err_msg)

        # Non-blocking execution
        threading.Thread(target=_worker, daemon=True).start()
