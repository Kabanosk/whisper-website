import os
import tempfile
import uuid

from loguru import logger
from stable_whisper import WhisperResult

from core.model_cache import get_model
from exceptions import ModelTranscriptionError
from schemas.transcription import TranscriptionRequest
from services.subtitles import make_srt_subtitles


def save_upload_to_temp(file_bytes: bytes) -> str:
    """Save uploaded file bytes to a temporary directory.

    :param file_bytes: Raw bytes of the uploaded audio file.
    :return: Path to the newly written temp file.
    """
    audio_file = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.mp3")
    with open(audio_file, "wb") as f:
        f.write(file_bytes)

    return audio_file


def save_output_to_temp(content: str, extension: str) -> str:
    """Save generated transcription file to temporary directory.

    :param content: Content to save in file.
    :param extension: Extension of the saved file.

    :return: Path to the written temp file.
    """
    generated_name = uuid.uuid4().hex
    subtitle_file = os.path.join(tempfile.gettempdir(), f"{generated_name}.{extension}")
    with open(subtitle_file, "w", encoding="utf-8") as f:
        f.write(content)

    return subtitle_file


def transcribe_audio(audio_file: str, model_type: str) -> WhisperResult:
    """Transcribe audio file using Whisper model.

    :param audio_file: Path to audio file.
    :param model_type: Type of Whisper model to use.

    :return: The transcription result object returned by the Whisper model.
    """
    try:
        model = get_model(model_type)
        result = model.transcribe(audio_file, regroup=False)
    except Exception as e:
        logger.exception(f"Error with transcription of: '{audio_file}', using model: '{model_type}'")
        raise ModelTranscriptionError(f"Transcription raised an error for model {model_type!r}: {e!r}") from e

    return result


def build_output_content(result: WhisperResult, request: TranscriptionRequest) -> str:
    """Build content in chosen type of subtitles.

    :param result: Result of the Whisper model transcription.
    :param request: Request sent by the user.

    :return: Content in the chosen type.
    """
    content = ""
    if not request.timestamps:
        content = result.text
    elif request.file_type == "srt":
        content = make_srt_subtitles(result.segments, request.translate_to, request.max_characters)
    elif request.file_type == "vtt":
        content = result.to_srt_vtt(vtt=True)

    return content
