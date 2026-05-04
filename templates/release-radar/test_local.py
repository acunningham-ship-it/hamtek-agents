"""
Local end-to-end test — no live GitHub webhook needed.

Run this after starting server.py:
    python server.py &
    python test_local.py

Or fire at an already-running server:
    python test_local.py --url http://your-server:5050
"""
import argparse
import json
import sys
from pathlib import Path

import requests

SAMPLE = json.loads(Path("sample_payload.json").read_text())


def test_webhook(base_url: str) -> None:
    print(f"[test] Posting sample release payload to {base_url}/webhook …")
    r = requests.post(
        f"{base_url}/webhook",
        json=SAMPLE,
        headers={"X-GitHub-Event": "release", "Content-Type": "application/json"},
        timeout=90,
    )
    print(f"[test] Status: {r.status_code}")
    data = r.json()
    print(f"[test] Response: {json.dumps(data, indent=2)}")

    if r.status_code != 202:
        print("[FAIL] Expected 202 Accepted")
        sys.exit(1)

    entry_id = data.get("id")
    print(f"\n[test] Fetching queue to verify entry {entry_id} …")
    q = requests.get(f"{base_url}/queue.json").json()
    match = next((e for e in q if e["id"] == entry_id), None)
    if not match:
        print("[FAIL] Entry not found in queue")
        sys.exit(1)

    print("\n[test] Generated drafts:")
    print(json.dumps(match["drafts"], indent=2))
    print(f"\n[PASS] Release Radar processed {match['repo']} {match['tag']} successfully.")
    print(f"       Open {base_url}/ to see the approval queue.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:5050")
    args = parser.parse_args()
    test_webhook(args.url)
