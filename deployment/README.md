# Deployment material

The Docker files start the same local development server described in
`docs/installation.md`; they do not turn it into a production service. The host
port binds to `127.0.0.1` by default. Build only after reviewing the source and
providing an approved production architecture.

```powershell
docker compose -f deployment/docker-compose.yml up --build
```

Before any non-local use, implement the production requirements in
`specification/security-specification.md`, select a database/scaling topology,
configure TLS/mTLS, backups, monitoring, secrets, authorization, rate limits,
and incident response. Docker build and daemon validation are **NOT RUN** in
this workspace.

