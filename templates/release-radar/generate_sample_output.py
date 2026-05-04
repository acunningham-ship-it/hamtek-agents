"""
Generate sample_output.json using the claude CLI.
This script is for building the demo asset — production uses server.py with ANTHROPIC_API_KEY.
"""
import json
import subprocess
import sys
from pathlib import Path

SAMPLE = json.loads(Path("sample_payload.json").read_text())
release_info = SAMPLE["release"]
repo = SAMPLE["repository"]["full_name"]

PROMPT = f"""You are a developer-relations writer. A new software release just shipped.

Repo: {repo}
Tag: {release_info["tag_name"]}
Title: {release_info["name"]}
Release notes:
{release_info["body"]}
Release URL: {release_info["html_url"]}

Write platform-specific announcement drafts. Return ONLY valid JSON with these keys:
{{
  "tweet_thread": ["tweet 1 (≤280 chars)", "tweet 2 (optional)", "tweet 3 (optional)"],
  "hn_post": "Show HN / Ask HN post — 1-3 paragraphs, plain text, dev-audience tone",
  "reddit_draft": {{
    "subreddit": "most relevant subreddit (e.g. programming, Python, webdev)",
    "title": "post title",
    "body": "post body markdown"
  }},
  "newsletter_paragraph": "1 paragraph suitable for a developer newsletter"
}}

Keep tweet_thread to 1-3 tweets. Be specific, not hype. Lead with the value."""

print("Calling Claude to generate drafts for sample release...")
result = subprocess.run(
    ["claude", "-p", PROMPT],
    capture_output=True, text=True, check=True
)

raw = result.stdout.strip()
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
    raw = raw.strip()
    if "```" in raw:
        raw = raw[:raw.index("```")]

drafts = json.loads(raw)

output = {
    "id": "1746288000000",
    "repo": repo,
    "tag": release_info["tag_name"],
    "release_name": release_info["name"],
    "release_url": release_info["html_url"],
    "created_at": "2026-05-03T12:00:00Z",
    "status": "pending",
    "drafts": drafts
}

Path("sample_output.json").write_text(json.dumps(output, indent=2))
print("Wrote sample_output.json")
print(json.dumps(drafts, indent=2))
