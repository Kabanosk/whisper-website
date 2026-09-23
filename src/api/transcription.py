from fastapi import APIRouter, File, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask

from schemas.transcription import SubtitleFileType, TranscriptionRequest, WhisperModelType
from services.subtitles import DEFAULT_MAX_CHARACTERS
from services.transcription import build_output_content, save_output_to_temp, save_upload_to_temp, transcribe_audio
from utils import safe_remove

router = APIRouter()
template = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return template.TemplateResponse(request, "index.html", {"text": None})


@router.post("/download/")
def download_subtitle(
    request: Request,
    file: bytes = File(),
    model_type: WhisperModelType = Form(WhisperModelType.TINY),
    timestamps: bool = Form(False),
    filename: str = Form("subtitles"),
    file_type: SubtitleFileType = Form(SubtitleFileType.SRT),
    max_characters: int = Form(DEFAULT_MAX_CHARACTERS),
    translate_to: str = Form("no_translation"),
):
    transcription = TranscriptionRequest(
        model_type=model_type,
        timestamps=timestamps,
        filename=filename,
        file_type=file_type,
        max_characters=max_characters,
        translate_to=translate_to,
    )
    audio_file = save_upload_to_temp(file)

    try:
        result = transcribe_audio(audio_file, transcription.model_type)
    finally:
        safe_remove(audio_file)

    content = build_output_content(result, transcription)
    subtitle_file = save_output_to_temp(content, transcription.output_extension)

    return FileResponse(
        path=subtitle_file,
        media_type="application/octet-stream",
        filename=transcription.download_filename,
        background=BackgroundTask(safe_remove, subtitle_file),
    )
