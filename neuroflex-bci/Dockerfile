FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY data/sample/ data/sample/
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "neuroflex.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
