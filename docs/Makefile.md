All commands run inside Docker. The only exception is dependency management — those run locally to update `pyproject.toml` and `uv.lock`, then you rebuild the image.

Run `make help` anytime to see the full list with descriptions.

---

**Daily use:**

```bash
make up          # start all services (detached)
make down        # stop all services
make logs        # follow API logs
make shell       # bash inside the API container
make ps          # show running containers
```

**Database:**

```bash
make migrate                          # apply all pending migrations (runs in Docker)
make migrate-create msg="add users"   # generate a new migration (runs in Docker)
make migrate-down                     # roll back one migration (runs in Docker)
make migrate-history                  # show full migration history (runs in Docker)
make db-shell                         # psql inside the DB container
make redis-shell                      # redis-cli inside the Redis container
```

**Testing:**

All test commands run inside the API container. Integration tests need the ephemeral test database (`pricegrid-db-test`) — `make test`, `make test-integration`, and `make coverage` start it automatically via the `test` Docker Compose profile. Unit tests have no database dependency.

```bash
make test                                           # all tests — starts test DB automatically
make test-unit                                      # unit tests only — no test DB needed
make test-integration                               # integration tests — starts test DB automatically
make coverage                                       # all tests with coverage report
make test-file f=tests/unit/test_auth_service.py   # one specific file
```

**Code quality (all run in Docker):**

```bash
make lint          # ruff linter
make lint-fix      # ruff linter with auto-fix
make format        # ruff formatter
make format-check  # check formatting without applying
make typecheck     # mypy
```

**Dependency management (runs locally — exception to the Docker rule):**

These are the only commands that run on your host machine. They update `pyproject.toml` and `uv.lock`, which the Docker image is built from. After running any of these, rebuild the image.

```bash
make add pkg=httpx        # add a runtime dependency
make add-dev pkg=pytest   # add a dev-only dependency
make remove pkg=httpx     # remove a dependency
make install              # sync local .venv (for IDE support only)
```

Workflow for adding a dependency:

```bash
make add pkg=httpx   # updates pyproject.toml + uv.lock locally
make build           # rebuilds the Docker image with the new dep
make up              # restarts services
```

**Reset everything:**

```bash
make reset       # wipe volumes, rebuild images, start fresh
make clean       # remove Python cache files (__pycache__, .pyc, htmlcov, etc.)
make clean-all   # stop services + wipe volumes + remove cache files
make down-v      # stop all services and wipe all volumes
```
