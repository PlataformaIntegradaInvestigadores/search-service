FROM python:3.11-bookworm

WORKDIR /app

RUN useradd -m appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm
RUN python -c "import nltk; nltk.download('stopwords')"

COPY --chown=appuser:appuser . .

USER appuser
RUN python -c "from keybert import KeyBERT; KeyBERT()"

EXPOSE 8001

CMD ["gunicorn", "config.wsgi:application", "-b", "0.0.0.0:8001", "-w", "2", "--timeout", "300", "--preload"]
