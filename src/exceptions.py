import pydantic
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger


class TranscriptionError(Exception):
    """Base exception for errors with transcription"""


class ModelTranscriptionError(TranscriptionError):
    """Raised when the Whisper model fails to transcribe the audio."""


class TranslationError(TranscriptionError):
    """Raised when the translation module fails to translate the text."""


def register_exception_handlers(app: FastAPI):
    """Register app-wide handlers for transcription and validation errors."""

    @app.exception_handler(TranscriptionError)
    def handle_transcription_error(request: Request, exc: TranscriptionError) -> JSONResponse:
        logger.error("Transcription request failed: {}", exc)
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(pydantic.ValidationError)
    def handle_validation_error(request: Request, exc: pydantic.ValidationError) -> JSONResponse:
        logger.error("Bad values in the form. {}", exc)
        return JSONResponse(status_code=422, content={"detail": exc.errors()})
