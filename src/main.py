import ast
import asyncio
import subprocess

import srt as srt
from datetime import timedelta, datetime
from fastapi import FastAPI, Request, File, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import ffmpeg
import numpy as np
import whisper


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
def transcribe_time_stamps(filename: str, interval: str, model):
    interval = int(interval)
    timestamps = {}
    pos = 0

    args = ("ffprobe", "-show_entries", "format=duration", "-i", filename)
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    duration = float(output.decode("utf-8").split("\n")[1].split("=")[1])

    while duration > pos:
        result = model.transcribe(get_audio_buffer(filename, pos, interval))
        timestamps.update(
            {str(timedelta(seconds=pos)) + " --> " + str(timedelta(seconds=(pos + interval))): result["text"]})
        pos += interval

    string = ""
    for timestamp, text in timestamps.items():
        string += timestamp + text + "\n"
    return string, timestamps


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
    interval = super_data['interval']
    filename = super_data['filename']
    filetype = super_data['file_type']
    model = whisper.load_model(model_type)

    if interval == "" and filename == "":
        result = model.transcribe("audio.mp3")
        return template.TemplateResponse('index.html', {"request": request, "text": result['text']})
    else:
        if interval == "":
            interval = "10"
        result, timestamps = transcribe_time_stamps("audio.mp3", interval, model)

        srt_f = False
        if filename and filetype:
            srt_f = timestamps

        if srt_f:
            return template.TemplateResponse('index.html', {"request": request, "text": result, "file": srt_f,
                                                            "filename": filename, "filetype": filetype})
        else:
            return template.TemplateResponse('index.html', {"request": request, "text": result})


@app.get('/file-data/{filename}/{filetype}/{srt_s}')
def download_subtitles(filename, filetype, srt_s):
    srt_d = ast.literal_eval(srt_s)

    s = make_srt_subtitles(srt_d)

    return Response(content=s, media_type='application/octet-stream',
                    headers={'Content-Disposition': f'attachment; filename="{filename}.{filetype}"'})
