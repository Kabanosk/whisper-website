import ast
import asyncio
import subprocess
from pprint import pprint

import srt as srt
from datetime import timedelta, datetime
from fastapi import FastAPI, Request, File, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import ffmpeg
import numpy as np
import stable_whisper


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


def make_srt_subtitles(timestamps: dict):
    subtitles = []
    for i, (time_str, text) in enumerate(timestamps.items(), start=1):
        start_time_str, end_time_str = time_str.split(" --> ")
        start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
        end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()
        subtitle = srt.Subtitle(
            index=i,
            start=timedelta(
                hours=start_time.hour, minutes=start_time.minute, seconds=start_time.second,
                microseconds=start_time.microsecond
            ),
            end=timedelta(
                hours=end_time.hour, minutes=end_time.minute, seconds=end_time.second, microseconds=end_time.microsecond
            ),
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
def add_audio(request: Request, file: bytes = File()):
    with open('audio.mp3', 'wb') as f:
        f.write(file)

    data = request.form()
    super_data = asyncio.run(data)
    model_type = super_data['model_type']
    try:
        timestamps = super_data['timestamps']
    except:
        timestamps = None
    filename = super_data['filename']
    filetype = super_data['file_type']

    model = stable_whisper.load_model(model_type)
    result = model.transcribe("audio.mp3", regroup=False)

    if not timestamps and filename == "":
        return template.TemplateResponse('index.html', {"request": request, "text": result.text})
    else:
        timestamps_text = transcribe_time_stamps(result.segments)

        if filename and filetype:
            result.to_srt_vtt(f"../data/{filename}.{filetype}")
            return template.TemplateResponse('index.html', {"request": request, "text": ""})
        elif timestamps:
            return template.TemplateResponse('index.html', {"request": request, "text": timestamps_text})

