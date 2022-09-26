import io

from fastapi import FastAPI, Request, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import librosa

from whisper import whisper

app = FastAPI()

model = whisper.load_model('base')

app.mount('/static', StaticFiles(directory='static'), name='static')
template = Jinja2Templates(directory='templates')


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return template.TemplateResponse('index.html',  {"request": request, "text": None})


@app.post('/')
def add_audio(request: Request, file: bytes = File()):
    with open('audio.mp3', 'wb') as f:
        f.write(file)
    result = model.transcribe("audio.mp3")

    return template.TemplateResponse('index.html',  {"request": request, "text": result['text']})
