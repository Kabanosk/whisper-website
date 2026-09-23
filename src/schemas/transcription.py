import os
import re
from enum import StrEnum, auto

from pydantic import BaseModel, Field, field_validator

from services.subtitles import DEFAULT_MAX_CHARACTERS


class WhisperModelType(StrEnum):
    """Enum for Whisper model types"""

    TURBO = auto()
    TINY = auto()
    BASE = auto()
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()


class SubtitleFileType(StrEnum):
    """Enum for subtitle file extensions"""

    SRT = auto()
    VTT = auto()


class TranscriptionRequest(BaseModel):
    """Validated parameters for a single transcription request."""

    model_type: WhisperModelType = WhisperModelType.TINY
    timestamps: bool = False
    filename: str = "subtitles"
    file_type: SubtitleFileType = SubtitleFileType.SRT
    max_characters: int = Field(default=DEFAULT_MAX_CHARACTERS, gt=0, le=500)
    translate_to: str = "no_translation"

    @field_validator("filename")
    @classmethod
    def sanitize_filename(cls, value: str) -> str:
        safe_filename = re.sub(r"[^A-Za-z0-9_.-]", "_", os.path.basename(value))
        safe_filename = os.path.splitext(safe_filename)[0]

        if not safe_filename:
            safe_filename = "subtitles"

        return safe_filename

    @property
    def output_extension(self) -> str:
        return self.file_type if self.timestamps else "txt"

    @property
    def download_filename(self) -> str:
        return f"{self.filename}.{self.output_extension}"
