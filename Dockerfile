# Genesis API — Railway / Docker (monorepo: backend + brain/kernel/agents)
FROM python:3.12-slim

WORKDIR /app

COPY dashboard/backend/requirements.txt /app/dashboard/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/dashboard/backend/requirements.txt

COPY brain /app/brain
COPY kernel /app/kernel
COPY agents /app/agents
COPY dashboard/backend /app/dashboard/backend

WORKDIR /app/dashboard/backend

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
