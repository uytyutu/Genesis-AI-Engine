# ANON — production image (SQLite + Next standalone)
FROM node:22-bookworm-slim AS deps
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 make g++ \
  && rm -rf /var/lib/apt/lists/*
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-bookworm-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 make g++ \
  && rm -rf /var/lib/apt/lists/*
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm run build

FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3100
ENV HOSTNAME=0.0.0.0
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd -r anon && useradd -r -g anon anon \
  && mkdir -p /app/data && chown -R anon:anon /app

COPY --from=builder --chown=anon:anon /app/public ./public
COPY --from=builder --chown=anon:anon /app/.next/standalone ./
COPY --from=builder --chown=anon:anon /app/.next/static ./.next/static

# better-sqlite3 native module lives under node_modules in standalone
USER anon
EXPOSE 3100
VOLUME ["/app/data"]
CMD ["node", "server.js"]
