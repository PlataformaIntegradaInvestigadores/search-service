FROM python:3.11-bookworm

WORKDIR /app

RUN useradd -m appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm
RUN python -c "import nltk; nltk.download('stopwords')"

COPY --chown=appuser:appuser . .

# centinela_logs/ and resources/ are in .dockerignore (the server bind-mounts the
# checkout over /app), so the image has no log directory: without it Django fails
# at startup with PermissionError because appuser cannot create it under /app.
RUN mkdir -p /app/centinela_logs && chown appuser:appuser /app/centinela_logs

USER appuser
RUN python -c "from keybert import KeyBERT; KeyBERT()"

EXPOSE 8001

# /health/ answers 503 when Neo4j or MongoDB are down. The start period covers
# the time the workers need to load the models in the background.
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health/', timeout=5)"

CMD ["gunicorn", "config.wsgi:application", "-c", "config/gunicorn.conf.py", "-b", "0.0.0.0:8001", "-w", "2", "--timeout", "300", "--preload"]
