FROM astral/uv:python3.13-bookworm-slim

COPY . /app
WORKDIR /app

RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "python", "run.py"]