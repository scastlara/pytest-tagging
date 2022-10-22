FROM python:3.10-slim

RUN apt update && apt install -y curl build-essential
RUN curl -sSL https://install.python-poetry.org | python -

COPY pytest_tagging pytest_tagging
COPY pyproject.toml poetry.lock Makefile README.md ./
COPY tests tests
ENV PATH=/root/.local/bin:$PATH
RUN make .venv
ENTRYPOINT [ "/bin/sh" ]
