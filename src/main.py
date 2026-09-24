from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.transcription import router
from exceptions import register_exception_handlers

app = FastAPI()

app.include_router(router)
register_exception_handlers(app)
app.mount("/static", StaticFiles(directory="static"), name="static")
