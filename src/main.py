import os
import ast
import asyncio
import subprocess
from pprint import pprint
from pathlib import Path
import srt as srt
from datetime import timedelta, datetime
from fastapi import FastAPI, Request, File, Response, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import ffmpeg
import numpy as np
import stable_whisper
from typing import Optional
import shutil



# a function that takes a file and a start and length timestamps, and will return the audio data in that section as a
# np array which the model's transcribe function can take
def get_audio_buffer(filename: str, start: int, length: int):
    out, _ = (
        ffmpeg.input(filename, threads=0)
        .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=16000, ss=start, t=length)
        .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
    )

    return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0


# a function that takes a file and an interval that deterimines the distance between each timestamp in the
# outputted dictionary
def transcribe_time_stamps(segments: list):
    string = ""
    for seg in segments:
        string += " ".join([str(seg.start), "->", str(seg.end), ": ", seg.text.strip(), "\n"])
    return string


def make_srt_subtitles(segments: list):
    subtitles = []
    for i, seg in enumerate(segments, start=1):
        start_time = seg.start
        end_time = seg.end
        text = seg.text.strip()

        subtitle = srt.Subtitle(
            index=i,
            start=timedelta(seconds=start_time),
            end=timedelta(seconds=end_time),
            content=text
        )
        subtitles.append(subtitle)

    return srt.compose(subtitles)

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')
template = Jinja2Templates(directory='templates')


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return template.TemplateResponse('index.html', {"request": request, "text": None})


@app.post('/')
def add_audio(
        request: Request,
        file: bytes = File(),
        model_type: str = Form("tiny"),
        timestamps: Optional[str] = Form("False"),
        filename: str = Form(""),
        file_type: str = Form("srt"),
):
    with open('audio.mp3', 'wb') as f:
        f.write(file)

    model = stable_whisper.load_model(model_type)
    result = model.transcribe("audio.mp3", regroup=False)

    if not timestamps and filename == "":
        return template.TemplateResponse('index.html', {"request": request, "text": result.text})
    else:
        timestamps_text = transcribe_time_stamps(result.segments)

        if filename and file_type:
            result.to_srt_vtt(f"../data/{filename}.{file_type}")
            return template.TemplateResponse('index.html', {"request": request, "text": ""})
        elif timestamps == "True":
            return template.TemplateResponse('index.html', {"request": request, "text": timestamps_text})



# Added the following feature to automatically download the transcripted file. The file will download in the web browser of the user. 
@app.post('/download/')
async def download_subtitle(request: Request, file: bytes = File(), model_type: str = "tiny", timestamps: Optional[str] = Form("False"), filename: str = "subtitles", file_type: str = "srt"):

    # Save the uploaded file
    with open('audio.mp3', 'wb') as f:
        f.write(file)

    # Load the model and transcribe the audio
    model = stable_whisper.load_model(model_type)
    result = model.transcribe("audio.mp3", regroup=False)

    # Create a timestamps text if needed
    if timestamps == "True":
        timestamps_text = transcribe_time_stamps(result.segments)

    # Create the subtitle file
    if file_type == "srt":
        subtitle_file = f"{filename}.srt"
        with open(subtitle_file, "w") as f:
            if timestamps:
                f.write(make_srt_subtitles(result.segments))
            else:
                f.write(result.text)
    elif file_type == "vtt":
        subtitle_file = f"{filename}.vtt"
        with open(subtitle_file, "w") as f:
            if timestamps:
                f.write(result.to_vtt())
            else:
                f.write(result.text)

    # Create a streaming response with the file
    path = Path(subtitle_file)
    media_type = "application/octet-stream"
    response = StreamingResponse(path.open('rb'), media_type=media_type, headers={'Content-Disposition': f'attachment;filename={subtitle_file}'})

    # Clean up the generated file after sending the response
    shutil.move(subtitle_file, path)  # This line ensures that the file is not deleted prematurely
    os.remove(subtitle_file)

    return response