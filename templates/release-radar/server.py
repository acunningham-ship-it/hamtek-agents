"""
Release Radar — GitHub release webhook → multi-platform post drafts → 1-click approval queue.

Set ANTHROPIC_API_KEY and WEBHOOK_SECRET in your environment before starting.
Run: python server.py
Then point your GitHub webhook to http://your-server:5050/webhook
"""
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

import anthropic
from flask import Flask, abort, jsonify, render_template, request

app = Flask(__name__)

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
QUEUE_FILE = Path("queue.json")


def load_queue() -> list[dict]:
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return []


def save_queue(queue: list[dict]) -> None:
    QUEUE_FILE.write_text(json.dumps(queue, indent=2))


def verify_signature(payload: bytes, signature: str) -> bool:
    if not WEBHOOK_SECRET:
        return True  # Skip verification in dev mode
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _call_claude_cli(prompt: str) -> str:
    """Fallback: call claude CLI when no ANTHROPIC_API_KEY is set (dev/demo mode)."""
    import subprocess
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, check=True, timeout=120
    )
    return result.stdout.strip()


def generate_drafts(release: dict) -> dict:
    """Call Claude to draft posts for each platform."""
    if not API_KEY:
        # Dev mode: use claude CLI
        use_cli = True
    else:
        use_cli = False
        client = anthropic.Anthropic(api_key=API_KEY)

    repo_name = release.get("repository", "")
    tag = release.get("tag_name", "")
    title = release.get("name", tag)
    body = release.get("body", "").strip()
    url = release.get("html_url", "")

    prompt = f"""You are a developer-relations writer. A new software release just shipped.

Repo: {repo_name}
Tag: {tag}
Title: {title}
Release notes:
{body or "(no release notes)"}
Release URL: {url}

Write platform-specific announcement drafts. Return ONLY valid JSON with these keys:
{{
  "tweet_thread": ["tweet 1 (≤280 chars)", "tweet 2 (optional)", "tweet 3 (optional)"],
  "hn_post": "Ask HN / Show HN post — 1-3 paragraphs, plain text, dev-audience tone",
  "reddit_draft": {{
    "subreddit": "most relevant subreddit (e.g. programming, Python, webdev)",
    "title": "post title",
    "body": "post body markdown"
  }},
  "newsletter_paragraph": "1 paragraph suitable for a developer newsletter"
}}

Keep tweet_thread to 1–3 tweets. Be specific, not hype. Lead with the value."""

    if use_cli:
        raw = _call_claude_cli(prompt)
    else:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
        if "```" in raw:
            raw = raw[: raw.index("```")]

    return json.loads(raw)


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Hub-Signature-256", "")
    if WEBHOOK_SECRET and not verify_signature(request.data, signature):
        abort(403, "Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event != "release":
        return jsonify({"status": "ignored", "reason": f"event={event}"}), 200

    payload = request.json
    action = payload.get("action", "")
    if action != "published":
        return jsonify({"status": "ignored", "reason": f"action={action}"}), 200

    release = payload["release"]
    repo = payload["repository"]["full_name"]

    print(f"  Generating drafts for {repo} {release['tag_name']}…")
    drafts = generate_drafts(
        {
            "repository": repo,
            "tag_name": release["tag_name"],
            "name": release.get("name", ""),
            "body": release.get("body", ""),
            "html_url": release["html_url"],
        }
    )

    entry = {
        "id": str(int(time.time() * 1000)),
        "repo": repo,
        "tag": release["tag_name"],
        "release_name": release.get("name", release["tag_name"]),
        "release_url": release["html_url"],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "pending",
        "drafts": drafts,
    }

    queue = load_queue()
    queue.insert(0, entry)
    save_queue(queue)

    print(f"  Queued entry {entry['id']}")
    return jsonify({"status": "queued", "id": entry["id"]}), 202


@app.route("/")
def index():
    return render_template("queue.html", queue=load_queue())


@app.route("/approve/<entry_id>", methods=["POST"])
def approve(entry_id: str):
    queue = load_queue()
    for entry in queue:
        if entry["id"] == entry_id:
            entry["status"] = "approved"
    save_queue(queue)
    return jsonify({"status": "approved"})


@app.route("/dismiss/<entry_id>", methods=["POST"])
def dismiss(entry_id: str):
    queue = load_queue()
    for entry in queue:
        if entry["id"] == entry_id:
            entry["status"] = "dismissed"
    save_queue(queue)
    return jsonify({"status": "dismissed"})


@app.route("/queue.json")
def queue_json():
    return jsonify(load_queue())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    debug = os.environ.get("DEBUG", "").lower() in ("1", "true")
    print(f"Release Radar listening on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
