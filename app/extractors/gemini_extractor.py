import base64
import logging
import time

import httpx

from app.extractors.base import ExtractionError
from app.extractors.prompt import PROMPT, parse_model_reply
from app.schemas import ReceiptData

logger = logging.getLogger(__name__)

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Rate limits and brief outages are worth one more try; other errors are not.
RETRYABLE = {429, 500, 503}
ATTEMPTS = 3


class GeminiExtractor:
    """Sends the receipt image to Google Gemini over its REST API (has a free tier)."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def extract(self, image_bytes: bytes, content_type: str) -> ReceiptData:
        body = {
            "contents": [
                {
                    "parts": [
                        {"text": PROMPT},
                        {
                            "inline_data": {
                                "mime_type": content_type,
                                "data": base64.b64encode(image_bytes).decode(),
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }
        reply = self._post(body)
        return parse_model_reply(self._reply_text(reply))

    def _post(self, body: dict) -> dict:
        url = API_URL.format(model=self.model)
        # The key goes in a header, not the URL, so it never ends up in logs.
        headers = {"x-goog-api-key": self.api_key}

        for attempt in range(1, ATTEMPTS + 1):
            try:
                response = httpx.post(url, json=body, headers=headers, timeout=60)
            except httpx.HTTPError as exc:
                raise ExtractionError(f"Could not reach the Gemini API: {exc}") from exc

            if response.status_code == 200:
                return response.json()

            if response.status_code in RETRYABLE and attempt < ATTEMPTS:
                time.sleep(2 * attempt)
                continue

            logger.error("Gemini returned %s: %s", response.status_code, response.text[:500])
            raise ExtractionError(self._error_message(response))

        raise ExtractionError("The Gemini API did not respond.")

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        try:
            detail = response.json()["error"]["message"]
        except (ValueError, KeyError, TypeError):
            detail = "no details given"
        return f"Gemini API error {response.status_code}: {detail}"

    @staticmethod
    def _reply_text(reply: dict) -> str:
        try:
            parts = reply["candidates"][0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts)
        except (KeyError, IndexError, TypeError) as exc:
            raise ExtractionError("The Gemini API returned no answer for this image.") from exc
