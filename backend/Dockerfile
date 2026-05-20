FROM astral/uv:python3.13-bookworm-slim

COPY . /app
WORKDIR /app

RUN uv sync

ENV PORT=${PORT:-10000}

EXPOSE $PORT

CMD ["uv", "run", "python", "run.py"]