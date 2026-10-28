# W3-A3: Containerized Task API on PostgreSQL

FastAPI task API backed by a real PostgreSQL server running in Docker. One command (`docker compose up`) starts the API and the database together. Data survives restarts because it lives in a Docker volume.

Part of the FlyRank Internship Backend Track, Week 1 (A3). Storage history in this repo: in-memory (A1) -> SQLite file (A2) -> Postgres in Docker (A3).

## Run it with one command

```bash
cp .env.example .env        # then edit POSTGRES_PASSWORD (and the same value inside DATABASE_URL)
docker compose up --build
```

API: http://localhost:8000 (interactive docs at `/docs`).

Stop with `Ctrl+C`, or `docker compose down`. Data is kept in the `taskdata` volume. Use `docker compose down -v` only if you want to wipe the database.

### Run the app locally against the Dockerized database

```bash
docker compose up -d db
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Configuration

| Variable | Where it lives | Purpose |
|---|---|---|
| `POSTGRES_PASSWORD` | `.env` | Password for the `postgres` user; read by compose |
| `DATABASE_URL` | `.env` (local runs) | Connection string; compose overrides it to point at host `db` |

`.env` is git-ignored. `.env.example` is committed with placeholder values. Compose refuses to start if `POSTGRES_PASSWORD` is missing.

## Endpoints

| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/tasks` | 200 list of tasks | |
| GET | `/tasks/{id}` | 200 task | 404 |
| POST | `/tasks` | 201 created task | 400 blank title |
| PUT | `/tasks/{id}` | 200 updated task (partial update) | 404 |
| DELETE | `/tasks/{id}` | 204 no content | 404 |

Errors return JSON in the form `{"detail": "..."}`, as in A2.

Example:

```bash
$ curl -i -X POST localhost:8000/tasks -H 'Content-Type: application/json' -d '{"title":"Ship A3"}'
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Ship A3","done":false}
```

## Architecture

- `repository.py` is the only module that talks to the database. It holds the connection logic, table creation, seeding, and every SQL statement, all using parameterized queries (`%s` placeholders).
- `main.py` contains the HTTP routes. They call the repository and map its results to status codes.
- `Dockerfile` builds the API image. `compose.yaml` defines two services: `db` (official `postgres:16` image with a volume and a health check) and `api`, which waits for `db` to be healthy before starting.

### What changed from A2, honestly

The A2 routes contained raw SQLite calls, so I could not swap storage without touching them. In A3 the SQL moved into `repository.py` and the routes now call it. The endpoints, status codes, validation rules, and response shapes are unchanged. The `sqlite3` code is gone.

## Persistence check

1. Create a task: `curl -X POST localhost:8000/tasks -H 'Content-Type: application/json' -d '{"title":"Persist me"}'`
2. Stop and restart everything: `docker compose down` then `docker compose up`
3. `curl localhost:8000/tasks` still shows "Persist me".

Seed-once is verified separately: restarting the API process three times against the same database kept the row count stable (no duplicate seeds).

## Database

```bash
docker compose exec db psql -U postgres -d tasks -c "SELECT * FROM tasks;"
```

Screenshot of `\dt` and `SELECT * FROM tasks;`: _add here_

## AI vs me

_To be written: the prompt used to generate an AI version, its differences from this implementation, and what the prompt missed._
