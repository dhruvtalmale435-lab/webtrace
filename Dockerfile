FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN pip install --no-cache-dir -r requirements.txt && python -m playwright install --with-deps chromium
COPY backend/ ./backend/
COPY --from=frontend /build/dist ./frontend/dist
ENV WEBTRACE_DATA_DIR=/data
RUN mkdir /data && useradd --create-home webtrace && chmod -R a+rX /ms-playwright && chown -R webtrace:webtrace /data /app /home/webtrace
USER webtrace
EXPOSE 8000
CMD ["python", "-m", "backend.serve"]
