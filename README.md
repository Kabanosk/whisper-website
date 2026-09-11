# whisper-website

A simple, self-hosted web app for turning audio into text and subtitles, powered by [OpenAI's Whisper](https://github.com/openai/whisper). Upload a file, pick a model, and download `.srt`, `.vtt`, or plain `.txt` - with optional translation.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9-blue.svg)

## Features

- Transcription with any Whisper model size (`tiny` → `large`)
- Export as `.srt`, `.vtt`, or plain `.txt`
- Optional timestamps - plain text export when they're off
- Optional translation of the transcript into another language
- No cloud dependency for transcription - everything runs on your own machine

## Quick start (Docker Compose)

This is the recommended way to run the app - it also keeps downloaded Whisper models cached between restarts.

1. Install [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/)
2. Clone the repo:
   ```bash
   git clone https://github.com/Kabanosk/whisper-website.git
   cd whisper-website
   ```
3. Start the app:
   ```bash
   docker compose up -d
   ```
4. Open [http://127.0.0.1](http://127.0.0.1)

To stop it: `docker compose down`. Your downloaded models stay cached in a Docker volume, so the next `up` won't re-download them.

## Quick start (local, no Docker)

1. Clone the repo and go into it:
   ```bash
   git clone https://github.com/Kabanosk/whisper-website.git
   cd whisper-website
   ```
2. Install dependencies with [uv](https://docs.astral.sh/uv/) - this also creates the virtual environment:
   ```bash
   uv sync
   ```
3. Run it:
   ```bash
   cd src
   uv run run.py
   ```
4. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) if it doesn't open automatically

You'll also need [ffmpeg](https://ffmpeg.org/download.html) installed and available on your `PATH` for this route - the Docker image already includes it.

## License

[MIT](LICENSE)