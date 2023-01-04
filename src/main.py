import io
import asyncio

from fastapi import FastAPI, Request, File, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import whisper
import ffmpeg
import numpy as np
import traceback
from datetime import timedelta


# a function that takes a file and a start and length timestamps, and will return the audio data in that section as a np array 
# which the model's transcribe function can take
def getAudioBuffer(file, start, length):

    out, _ = (
                ffmpeg.input(file, threads=0)
                .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=16000, ss=start, t=length)
                .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
            )

    return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0

# a function that takes a file and an interval that deterimines the distance between each timestamp in the outputted dictionary
def transcribeTimeStamps(file, interval, model):
    interval = int(interval)
    dict = {}
    pos = 0
    try:
        while(1):
            result = model.transcribe(getAudioBuffer(file, pos, interval))
            dict.update({ str(timedelta(seconds=(pos))) + " -> " + str(timedelta(seconds=(pos+interval))) : result["text"]})
            pos = pos + interval
    except:
        traceback.print_exc()
        stringgy = ""
        for timestamp, text in dict.items():
            stringgy = stringgy + timestamp + text + "\n"
        return stringgy




app = FastAPI()


app.mount('/static', StaticFiles(directory='static'), name='static')
template = Jinja2Templates(directory='templates')


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return template.TemplateResponse('index.html',  {"request": request, "text": None})


@app.post('/')
def add_audio(request: Request, file: bytes = File()):
    with open('audio.mp3', 'wb') as f:
        f.write(file)
    
    data = request.form()
    super_data = asyncio.run(data)
    model_type = super_data['model_type']
    interval = super_data['interval']
    model = whisper.load_model(model_type)

    if interval == "":
        result = model.transcribe("audio.mp3")
        return template.TemplateResponse('index.html',  {"request": request, "text": result['text']})
    else:
        result = transcribeTimeStamps("audio.mp3", interval, model)
        print(result)
        return template.TemplateResponse('index.html',  {"request": request, "text": result})


