import os
import re
import tempfile
import uuid

from fastapi import FastAPI, File, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask

from model_cache import get_model
from utils import DEFAULT_MAX_CHARACTERS, make_srt_subtitles, safe_remove

app = FastAPI(debug=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
template = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return template.TemplateResponse(request, "index.html", {"text": None})


@app.post("/download/")
def download_subtitle(
    request: Request,
    file: bytes = File(),
    model_type: str = Form("tiny"),
    timestamps: bool = Form(False),
    filename: str = Form("subtitles"),
    file_type: str = Form("srt"),
    max_characters: int = Form(DEFAULT_MAX_CHARACTERS),
    translate_to: str = Form("no_translation"),
):
    if file_type not in ("srt", "vtt"):
        file_type = "srt"

    audio_file = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.mp3")
    with open(audio_file, "wb") as f:
        f.write(file)

    try:
        model = get_model(model_type)
        result = model.transcribe(audio_file, regroup=False)
    finally:
        safe_remove(audio_file)

    safe_filename = re.sub(r"[^A-Za-z0-9_.-]", "_", os.path.basename(filename))
    safe_filename = os.path.splitext(safe_filename)[0]

    if not safe_filename:
        safe_filename = "subtitles"

    output_extension = file_type if timestamps else "txt"

    generated_name = uuid.uuid4().hex
    subtitle_file = os.path.join(
        tempfile.gettempdir(), f"{generated_name}.{output_extension}"
    )

    with open(subtitle_file, "w", encoding="utf-8") as f:
        if not timestamps:
            f.write(result.text)
        elif file_type == "srt":
            f.write(make_srt_subtitles(result.segments, translate_to, max_characters))
        elif file_type == "vtt":
            f.write(result.to_vtt())

    download_filename = f"{safe_filename}.{output_extension}"

    return FileResponse(
        path=subtitle_file,
        media_type="application/octet-stream",
        filename=download_filename,
        background=BackgroundTask(safe_remove, subtitle_file),
    )
