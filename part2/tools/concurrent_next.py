
"""Test concurrent /next requests against a pre-filled queue."""

import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_URL = "http://localhost:8000"
COUNT = 200


def post(route, data=None):
    body = None
    headers = {}

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(
        BASE_URL + route,
        data=body if body is not None else b"",
        headers=headers,
        method="POST"
    )

    try:
        with urlopen(req, timeout=30) as res:
            return res.status, res.read().decode("utf-8")
    except HTTPError as error:
        return error.code, error.read().decode("utf-8")


def main():
    expected = [f"user-{i:03d}" for i in range(COUNT)]

    # Fill the queue before starting concurrent takes.
    for name in expected:
        status, _ = post("/join", {"name": name})
        if status != 200:
            raise RuntimeError(f"Failed to join {name}")

    # Call next concurrently.
    with ThreadPoolExecutor(max_workers=50) as pool:
        results = list(
            pool.map(lambda _: post("/next"), range(COUNT))
        )

    taken = [
        body for status, body in results if status == 200
    ]

    errors = [
        status for status, _ in results if status != 200
    ]

    final_status, final_body = post("/next")

    passed = (
        not errors
        and Counter(taken) == Counter(expected)
        and (final_status, final_body) == (404, "empty")
    )

    print(json.dumps({
        "expected": COUNT,
        "taken": len(taken),
        "duplicate_names": list(
            (Counter(taken) - Counter(expected)).elements()
        ),
        "missing_names": list(
            (Counter(expected) - Counter(taken)).elements()
        ),
        "errors": errors,
        "final_next": {
            "status": final_status,
            "body": final_body
        },
        "passed": passed
    }, indent=2))


if __name__ == "__main__":
    main()
