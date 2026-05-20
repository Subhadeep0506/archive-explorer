FROM astral/uv:python3.12-bookworm-slim

COPY . /app
WORKDIR /app

RUN uv sync

EXPOSE 8000

CMD ["python", "run.py"]