FROM node:24-alpine AS frontend-build

WORKDIR /workspace/web-dashboard

COPY web-dashboard/package.json web-dashboard/package-lock.json ./
RUN npm ci

COPY web-dashboard/index.html web-dashboard/vite.config.js ./
COPY web-dashboard/src ./src
RUN npm run build


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY web-dashboard/requirements.txt ./web-dashboard/requirements.txt
RUN pip install --no-cache-dir -r web-dashboard/requirements.txt

COPY web-dashboard/app_config.py ./web-dashboard/app_config.py
COPY web-dashboard/server.py ./web-dashboard/server.py
COPY web-dashboard/seed_transactions.py ./web-dashboard/seed_transactions.py
COPY web-dashboard/openapi.json ./web-dashboard/openapi.json
COPY web-dashboard/alembic.ini ./web-dashboard/alembic.ini
COPY web-dashboard/alembic ./web-dashboard/alembic
COPY --from=frontend-build /workspace/web-dashboard/dist ./web-dashboard/dist
RUN mkdir -p /app/output

EXPOSE 8787

WORKDIR /app/web-dashboard
CMD ["python", "server.py"]
