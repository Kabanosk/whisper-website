from datetime import timedelta
from typing import Optional

from fastapi import FastAPI, Request, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import ffmpeg
import numpy as np
import srt as srt
import stable_whisper
from deep_translator import GoogleTranslator

DEFAULT_MAX_CHARACTERS = 80


def get_audio_buffer(filename: str, start: int, length: int):
    """
    input: filename of the audio file, start time in seconds, length of the audio in seconds
    output: np array of the audio data which the model's transcribe function can take as input
    """
    out, _ = (
        ffmpeg.input(filename, threads=0)
        .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=16000, ss=start, t=length)
        .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
    )

    return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0


def transcribe_time_stamps(segments: list):
    """
    input: a list of segments from the model's transcribe function
    output: a string of the timestamps and the text of each segment
    """
    string = ""
    for seg in segments:
        string += " ".join([str(seg.start), "->", str(seg.end), ": ", seg.text.strip(), "\n"])
    return string


def split_text_by_punctuation(text: str, max_length: int):
    chunks = []
    while len(text) > max_length:

        split_pos = max(
            text.rfind(p, 0, max_length) for p in [",", ".", "?", "!"," "] if p in text[:max_length]
        )


        if split_pos == -1:
            split_pos = max_length


        chunks.append(text[:split_pos + 1].strip())
        text = text[split_pos + 1:].strip()

    if text:
        chunks.append(text)

    return chunks


def translate_text(text: str, translate_to: str):
    return GoogleTranslator(source='auto', target=translate_to).translate(text=text)


def make_srt_subtitles(segments: list,translate_to: str, max_chars: int):
    subtitles = []
    for i, seg in enumerate(segments, start=1):
        start_time = seg.start
        end_time = seg.end
        text = translate_text(seg.text.strip(), translate_to)

        text_chunks = split_text_by_punctuation(text, max_chars)

        duration = (end_time - start_time) / len(text_chunks)

        for j, chunk in enumerate(text_chunks):
            chunk_start = start_time + j * duration
            chunk_end = chunk_start + duration

            subtitle = srt.Subtitle(
                index=len(subtitles) + 1,
                start=timedelta(seconds=chunk_start),
                end=timedelta(seconds=chunk_end),
                content=chunk
            )
            subtitles.append(subtitle)

    return srt.compose(subtitles)


app = FastAPI(debug=True)

app.mount('/static', StaticFiles(directory='static'), name='static')
template = Jinja2Templates(directory='templates')


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return template.TemplateResponse('index.html', {"request": request, "text": None})


@app.post('/download/')
async def download_subtitle(
        request: Request,
        file: bytes = File(),
        model_type: str = Form("tiny"),
        timestamps: Optional[str] = Form("False"),
        filename: str = Form("subtitles"),
        file_type: str = Form("srt"),
        max_characters: int = Form(DEFAULT_MAX_CHARACTERS),
        translate_to: str = Form('spanish'),
):

    with open('audio.mp3', 'wb') as f:
        f.write(file)
    
    model = stable_whisper.load_model(model_type)
    result = model.transcribe("audio.mp3", regroup=False)

    subtitle_file = "subtitle.srt"

    if file_type == "srt":
        subtitle_file = f"{filename}.srt"
        with open(subtitle_file, "w") as f:
            if timestamps:
                f.write(make_srt_subtitles(result.segments, translate_to, max_characters))
            else:
                f.write(result.text)
    elif file_type == "vtt":
        subtitle_file = f"{filename}.vtt"
        with open(subtitle_file, "w") as f:
            if timestamps:
                f.write(result.to_vtt())
            else:
                f.write(result.text)


    media_type = "application/octet-stream"
    response = StreamingResponse(
        open(subtitle_file, 'rb'),
        media_type=media_type,
        headers={'Content-Disposition': f'attachment;filename={subtitle_file}'}
    )

    return response