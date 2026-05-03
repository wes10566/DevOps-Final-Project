FROM python:3.12-slim

WORKDIR /app

COPY PLSWORK.py .
COPY bgm022.ogg .

CMD ["python", "PLSWORK.py"]