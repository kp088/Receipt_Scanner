import base64
import logging

from openai import OpenAI, OpenAIError

from app.extractors.base import ExtractionError
from app.extractors.prompt import PROMPT, parse_model_reply
from app.schemas import ReceiptData

logger = logging.getLogger(__name__)


class OpenAIExtractor:
    """Sends the receipt image to an OpenAI vision model and validates the JSON reply."""

    def __init__(self, api_key: str, model: str) -> None:
        # The SDK retries rate limits and transient network errors for us.
        self.client = OpenAI(api_key=api_key, max_retries=2, timeout=60)
        self.model = model

    def extract(self, image_bytes: bytes, content_type: str) -> ReceiptData:
        encoded = base64.b64encode(image_bytes).decode()
        image_url = f"data:{content_type};base64,{encoded}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
            )
        except OpenAIError as exc:
            logger.exception("OpenAI request failed")
            raise ExtractionError(f"The AI service request failed: {exc}") from exc

        return parse_model_reply(response.choices[0].message.content or "")
