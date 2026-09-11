FROM python:3.13
WORKDIR /app

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

COPY pyproject.toml uv.lock ./

RUN pip install uv
RUN uv sync --frozen

COPY src/ /app

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
