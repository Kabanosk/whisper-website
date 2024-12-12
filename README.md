## Website which convert speech to text by Whisper model ([Official Repo](https://github.com/openai/whisper))

## Hosting website on localhost:

1. Clone the repo - `git clone git@github.com:Kabanosk/whisper-website.git`
2. Go to repo directory - `cd whisper-website`
3. Create virtual environment - `python3 -m venv venv`
4. Activate the environment - `source venv/bin/activate`/`. venv/bin/activate`
5. Install requirements - `pip install -r requirements.txt`
6. Go to src directory - `cd src`
7. Run the `run.py` file - `python3 run.py`
8. Go to your browser and type `http://127.0.0.1:8000/` if the browser doesn't open

## Run website on localhost with Docker
### First time
1. Install [Docker](https://docs.docker.com/engine/install/)
2. Clone the repo - `git clone git@github.com:Kabanosk/whisper-website.git`
3. Go to repo directory - `cd whisper-website`
4. Create Docker image - `docker build -t app .`
5. Run Docker container - `docker run --name app_container -p 80:80 app`
6. Go to your browser and type `http://127.0.0.1:80/`

### Next time

1. Start your Docker container - `docker start app_container`
2. Go to your browser and type `http://127.0.0.1:80/`
