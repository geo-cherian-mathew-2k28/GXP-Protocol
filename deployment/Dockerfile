FROM python:3.13-slim

WORKDIR /app
COPY . /app

RUN useradd --create-home --uid 10001 gxp && chown -R gxp:gxp /app
USER gxp

EXPOSE 8080
VOLUME ["/data"]

CMD ["python", "-m", "gxp.cli", "server", "--db", "/data/gxp.db", "--host", "0.0.0.0", "--port", "8080"]

