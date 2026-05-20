FROM astral/uv:python3.12-bookworm-slim

COPY . /app
WORKDIR /app

RUN uv sync --no-dev --no-cache --no-install-project

EXPOSE 8000

CMD ["python", "run.py"]