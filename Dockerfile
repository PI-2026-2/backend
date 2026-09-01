FROM alpine:3.23.5

RUN apk add --no-cache uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1

ENV UV_LINK_MODE=copy

ENV UV_TOOL_BIN_DIR=/usr/local/bin

ENV UV_LINK_MODE=copy

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []

CMD ["uv","run","fastapi" ,"dev","--host","0.0.0.0","app/main.py"]
