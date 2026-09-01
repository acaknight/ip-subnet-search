# Subnet IP Lookup API

An async REST API built with **FastAPI** and **SQLAlchemy 2.0** for logging user IP addresses and querying them by exact match, partial match, or CIDR subnet containment — using PostgreSQL's native `inet` type for correct, index-friendly network lookups.

## Overview

Storing and querying IP addresses as plain strings is a common but flawed pattern — it breaks down the moment you need subnet-aware queries (e.g. "find all logs from `192.168.1.0/24`"). This project uses PostgreSQL's native `INET`/`CIDR` types and the `<<=` containment operator to perform correct, efficient subnet matching directly at the database level, instead of relying on brittle string `LIKE` matching or filtering in application code.

## Features

- **Create user IP logs** — validated against strict IPv4/IPv6 formats via Pydantic before hitting the database.
- **Fetch log by ID** — simple primary-key lookup.
- **Subnet-aware IP search** — query using a CIDR block (e.g. `192.168.1.0/24`) and get back every log whose IP falls within that subnet, using Postgres's `<<=` containment operator rather than text matching.
- **Graceful error handling** — invalid IP/CIDR input returns a clean `400`/`422` instead of a raw database traceback; duplicate IPs return `409`.

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| DB driver | asyncpg |
| Database | PostgreSQL (`inet` column type) |
| Validation | Pydantic v2 (`IPvAnyAddress` / `IPvAnyNetwork`) |
| Server | Uvicorn |

## API Endpoints

### `GET /user_logs/{log_id}`
Fetch a single log entry by its integer ID.

- **200** — returns the matching log
- **404** — no log with that ID

### `GET /users_ip/{partial_ip:path}`
Search logs by IP or CIDR subnet. Accepts a slash (e.g. `10.0.0.0/8`), so the route uses the `:path` converter.

- **200** — returns all logs whose `ip_address` is contained within (or equal to) the given subnet
- **404** — no matches found
- Uses Postgres's `<<=` operator against the `inet` column for correct network-range matching (not string search).

**Example**
```
GET /users_ip/192.168.1.0/24
```

### `POST /create_user`
Create a new IP log entry.

**Request body**
```json
{
  "user_id": 129,
  "ip_address": "120.234.231.10"
}
```

- **200/201** — entry created
- **409** — IP address already exists (unique constraint)
- **422** — malformed IP/CIDR (rejected by Pydantic validation before reaching the DB)

## Getting Started

### Prerequisites
- Python 3.11+ (see note below on 3.14 + `greenlet` compatibility)
- PostgreSQL 12+

### Setup

```bash
git clone https://github.com/<your-username>/subnet-ip-lookup-api.git
cd subnet-ip-lookup-api

python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Environment variables

Create a `.env` file:

```
DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5432/<db_name>
```

### Run the server

```bash
uvicorn main:app --reload
```

API docs available at `http://127.0.0.1:8000/docs`.

## Design Notes

- IP addresses are stored using Postgres's native `INET` column type rather than plain text, enabling correct network-aware querying and allowing a GiST index (`inet_ops`) for performant subnet lookups at scale.
- Subnet input is validated with Pydantic (`IPvAnyAddress`/`IPvAnyNetwork`) at the API boundary, so malformed input (e.g. an invalid prefix length) is rejected early with a clear `422`, rather than surfacing as a raw database error.
- The lookup endpoint uses the `:path` converter to correctly accept CIDR notation containing a `/` in the URL.

## Known Environment Notes

- If running on very recent Python versions (e.g. 3.14), ensure `greenlet` has a compatible wheel installed — SQLAlchemy's async engine depends on it to bridge sync drivers into async execution.

## Possible Future Improvements

- Add pagination to `/users_ip/{partial_ip}` for large result sets.
- Add IPv6 test coverage.
- Add Alembic migrations for schema versioning.
- Add automated tests (pytest + httpx) covering valid/invalid IP and subnet inputs.