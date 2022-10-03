import webbrowser
import uvicorn
from time import sleep

from multiprocessing import Process

def open_browser():
    webbrowser.open('http://127.0.0.1:8000')

def run_localhost():
    uvicorn.run('main:app')


if __name__ == '__main__':
    open_browser_proc = Process(target=open_browser)
    run_localhost_proc = Process(target=run_localhost)

    run_localhost_proc.start()
    sleep(2)
    open_browser_proc.start()