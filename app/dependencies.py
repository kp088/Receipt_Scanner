from fastapi import Depends, HTTPException, status

from app.config import Settings, get_settings
from app.extractors.base import ReceiptExtractor
from app.extractors.mock_extractor import MockExtractor


def get_extractor(settings: Settings = Depends(get_settings)) -> ReceiptExtractor:
    """Pick the extraction provider named in the EXTRACTOR setting."""
    if settings.extractor == "mock":
        return MockExtractor()

    if settings.extractor == "openai":
        if not settings.openai_api_key:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "EXTRACTOR is set to 'openai' but OPENAI_API_KEY is missing.",
            )
        # Imported here so mock mode works even without the openai package configured.
        from app.extractors.openai_extractor import OpenAIExtractor

        return OpenAIExtractor(settings.openai_api_key, settings.openai_model)

    if settings.extractor == "gemini":
        if not settings.gemini_api_key:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "EXTRACTOR is set to 'gemini' but GEMINI_API_KEY is missing.",
            )
        from app.extractors.gemini_extractor import GeminiExtractor

        return GeminiExtractor(settings.gemini_api_key, settings.gemini_model)

    raise HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        f"Unknown EXTRACTOR '{settings.extractor}'. Use 'mock', 'gemini' or 'openai'.",
    )
