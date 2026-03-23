FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/adamtheturtle/literalizer-cli"
LABEL org.opencontainers.image.description="CLI for literalizer - convert data structures to native language literal syntax"
LABEL org.opencontainers.image.licenses="MIT"

ARG LITERALIZER_CLI_VERSION

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the package from PyPI with pinned version
RUN uv pip install --system --no-cache "literalizer-cli==${LITERALIZER_CLI_VERSION}"

ENTRYPOINT ["literalize"]
