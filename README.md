# Subnet IP Lookup API

An asynchronous REST API for recording user IP addresses and searching them by log ID, IP/CIDR containment, or partial host text.

The service is built with FastAPI, SQLAlchemy 2.0, asyncpg, and PostgreSQL's native `INET` type. CIDR lookups use PostgreSQL's network containment operator instead of trying to interpret IP ranges in application code.

## Features

- Create user-to-IP log entries.
- Fetch an individual log by its ID.
- Find addresses contained by an IPv4 or IPv6 network.
- Search the textual host portion of an address.
- Use an asynchronous database session throughout the request path.
- Manage the database schema with Alembic.
- Seed the database with batches of unique random IPv4 addresses.

## Tech stack

| Layer | Technology |
| --- | --- |
| API | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Validation | Pydantic v2 |
| Database | PostgreSQL |
| Database driver | asyncpg |
| Migrations | Alembic |
| ASGI server | Uvicorn |

## Project structure

```text
.
├── app
│   ├── db
│   │   ├── alembic
│   │   │   └── versions
│   │   ├── database.py       # Async engine, session factory, and dependency
│   │   └── seed_db.py        # Batch data seeder
│   ├── models
│   │   ├── module.py         # SQLAlchemy model
│   │   └── schemas.py        # Request schema
│   └── main.py               # FastAPI application and routes
├── alembic.ini
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11 or later
- PostgreSQL 12 or later
- A PostgreSQL database and user with permission to create tables, indexes, and functions

## Getting started

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure the database

Create a `.env` file in the project root:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/subnet_lookup
```

Replace the username, password, host, port, and database name with your own values. Do not commit credentials to source control.

Alembic currently reads its connection URL from `alembic.ini`, independently of `DATABASE_URL`. Set `sqlalchemy.url` in `alembic.ini` to the same async PostgreSQL URL before running migrations:

```ini
sqlalchemy.url = postgresql+asyncpg://postgres:password@localhost:5432/subnet_lookup
```

### 4. Apply migrations

```bash
alembic upgrade head
```

The initial migration creates the `user_logs` table, an index on `ip_address`, and the `safe_inet_cast(text)` PostgreSQL function used by the search endpoint.

### 5. Run the API

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API reference

### Create a user log

```http
POST /create_user_log
Content-Type: application/json
```

Request body:

```json
{
  "user_id": 129,
  "ip_address": "120.234.231.10"
}
```

Example request:

```bash
curl -X POST http://127.0.0.1:8000/create_user_log \
  -H "Content-Type: application/json" \
  -d '{"user_id":129,"ip_address":"120.234.231.10"}'
```

Example response:

```json
{
  "message": "Entry created successfully",
  "data": {
    "id": 1,
    "user_id": 129,
    "ip_address": "120.234.231.10"
  }
}
```

### Fetch a log by ID

```http
GET /user_logs/{log_id}
```

Example:

```bash
curl http://127.0.0.1:8000/user_logs/1
```

The endpoint returns `404 Not Found` when the ID does not exist.

### Search by IP, CIDR, or partial host text

```http
GET /users_ip/{partial_ip}
```

The route uses FastAPI's `path` converter, so CIDR values containing `/` can be passed directly in the URL.

Find every address within a subnet:

```bash
curl http://127.0.0.1:8000/users_ip/192.168.1.0/24
```

Find an exact address:

```bash
curl http://127.0.0.1:8000/users_ip/192.168.1.42
```

Search the host text:

```bash
curl http://127.0.0.1:8000/users_ip/168.1
```

Internally, the query matches rows when either:

1. `ip_address <<= safe_inet_cast(input)` is true; or
2. `host(ip_address) ILIKE '%input%'` is true.

`safe_inet_cast` converts malformed network input to `NULL`, preventing the containment branch from raising a PostgreSQL cast error. The text-search branch can still match the supplied input. The endpoint returns `404 Not Found` when neither branch finds a row.

## Database schema

The initial migration creates the following logical schema:

```sql
CREATE TABLE user_logs (
    id         INTEGER PRIMARY KEY,
    user_id    INTEGER NOT NULL,
    ip_address INET NOT NULL
);
```

Using `INET` allows PostgreSQL to understand address and network semantics. In particular, the `<<=` operator checks whether the stored address is contained by or equal to the supplied address/network.

## Seed sample data

The seeder generates 50,000 unique random IPv4 addresses by default and inserts them in batches of 5,000:

```bash
python -m app.db.seed_db
```

Adjust `TOTAL_RECORDS` and `BATCH_SIZE` in `app/db/seed_db.py` if a different data volume is required.

## Alembic commands

Create a migration after changing a model:

```bash
alembic revision --autogenerate -m "describe the change"
```

Apply all migrations:

```bash
alembic upgrade head
```

Roll back the most recent migration:

```bash
alembic downgrade -1
```

## Current implementation notes

- `UserLogCreate.ip_address` is currently typed as `str`; Pydantic therefore does not validate IP syntax before the insert. PostgreSQL rejects invalid `INET` values.
- The model declares `ip_address` as nullable, while the initial migration declares it non-nullable. Keep the ORM model and migration schema aligned before generating future migrations.
- The create endpoint catches `IntegrityError` and reports a duplicate-IP conflict, but the current model and migration do not define a unique constraint on `ip_address`. Duplicate addresses are therefore allowed unless the database has an additional constraint outside this migration.
- The generated index on `ip_address` is a regular PostgreSQL index. If subnet containment becomes a high-volume query, inspect the query plan and consider a GiST or SP-GiST operator-class index appropriate for the workload.
- Search responses are not paginated, so broad networks may return large result sets.
- The repository does not currently include an automated test suite.

## Suggested next steps

- Change the request field to `IPvAnyAddress` and add a response schema.
- Add a unique constraint if one IP address must map to only one log entry.
- Add pagination and deterministic ordering to search results.
- Add pytest coverage for IPv4, IPv6, CIDR, malformed input, duplicates, and empty results.
- Read `DATABASE_URL` in Alembic's `env.py` so application and migration configuration share one source of truth.
- Disable SQLAlchemy's `echo=True` outside local development.

## License

No license has been specified for this project.
