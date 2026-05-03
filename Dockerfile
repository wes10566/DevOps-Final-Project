FROM python:3.12-slim

WORKDIR /app

COPY PLZWORK.py .

CMD ["python", "PLZWORK.py"]