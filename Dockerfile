FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git-lfs libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY webapp/requirements-nube.txt /tmp/requirements-nube.txt
RUN python -m pip install --upgrade pip \
    && pip install --extra-index-url https://download.pytorch.org/whl/cpu -r /tmp/requirements-nube.txt

COPY . /app

ENV RFDETR_CKPT=/app/checkpoint_best_regular.pth

EXPOSE 7860

CMD ["sh", "-c", "uvicorn webapp.app:app --host 0.0.0.0 --port ${PORT}"]