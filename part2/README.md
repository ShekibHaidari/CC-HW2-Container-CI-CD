
# Lab Queue — Part 2

## Student Information

- Name: Ahmad Shekib Haidari
- Student ID: 40231445
- Course: Cloud Computing

## Project Description

This project implements a file-based FIFO queue using Python.

The application provides three HTTP endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Returns `ok` |
| POST | /join | Adds a person and returns a ticket number |
| POST | /next | Removes and returns the first person |

The application stores its queue in `/data/queue.txt`.

## Requirements

- Docker Engine
- Docker Compose
- Python 3
- pytest for local testing

## Run Tests

From the `part2` directory:

```bash
python -m pip install -r requirements-dev.txt
pytest
```

Expected result: 13 tests passed.

## Build and Run

From the `part2` directory:

```bash
docker compose up -d --build --scale app=3
```

Check running containers:

```bash
docker compose ps
```

Check API health:

```bash
curl http://localhost:8000/health
```

Expected response:

```text
ok
```

## API Examples

Join the queue:

```bash
curl -X POST http://localhost:8000/join \
  -H "Content-Type: application/json" \
  -d '{"name":"Ali"}'
```

Take the next person:

```bash
curl -X POST http://localhost:8000/next
```

When the queue is empty, `/next` returns
HTTP 404 with the body `empty`.

## Docker Architecture

The application uses:

- Three Python application replicas
- An Nginx reverse proxy
- A shared Docker named volume

Only Nginx publishes the application port
to the host machine.

The application replicas use the same
queue file through the shared volume.

## Persistent Storage

Queue data is stored in a named Docker
volume mounted at `/data`.

Removing and recreating an application
container does not remove queue data.

Do not use `docker compose down -v`
when stored queue data must be preserved.

## Race Condition

The initial implementation had no locking.

With 200 concurrent join requests:

- Successful HTTP requests: 200
- Recovered names: 5
- Missing names: 195
- Test result: FAILED

The implementation was fixed using:

- `fcntl.flock` with a shared lock file
- An exclusive lock covering read and write
- A temporary file and `os.replace`
  for safe queue updates in `take`

After the fix:

- Successful HTTP requests: 200
- Recovered names: 200
- Missing names: 0
- Duplicate tickets: 0
- Test result: PASSED

## Concurrency Tests

Start with an empty test queue.

Run the concurrent join test:

```bash
python tools/concurrent_join.py \
  --url http://localhost:8000 --drain
```

Run the concurrent take test:

```bash
python tools/concurrent_next.py
```

The second test also requires an initially
empty queue and fills it before taking names.

## Git History

Initial implementation without locking:

`4e7046a`

Implementation with file locking:

`8f8b21b`

## Stop Containers

```bash
docker compose down
```

This stops and removes containers while
preserving the named volume.
