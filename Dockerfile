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
ENV GENESIS_ENV=production
# Public Launch defaults (override in Railway Variables if domain changes)
# Never ship retired Vercel preview as the commercial storefront.
ENV GENESIS_PUBLIC_URL=https://beta.genesis-ai-engine.com
ENV GENESIS_CORS_ORIGINS=https://beta.genesis-ai-engine.com

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}"]
