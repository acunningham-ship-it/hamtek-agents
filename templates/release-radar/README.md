# 📡 Release Radar

**Ship something? Let the internet know automatically.**

GitHub release → tweet thread + HN post + Reddit draft + newsletter paragraph, all in one webhook. Drafts land in a 1-click approval queue. Nothing posts without your sign-off.

**Price: $49 (one-time)**  
Part of the [HamTek Agents](https://acunningham-ship-it.github.io/hamtek-agents/) template store.

---

## What it does

1. You publish a GitHub release
2. GitHub fires a webhook to your Release Radar server
3. Claude reads your release notes and generates platform-specific drafts:
   - 𝕏 tweet thread (1-3 tweets, dev-native tone)
   - 🔶 Hacker News post (Show HN / Ask HN format)
   - 🤖 Reddit draft (picks the right subreddit, markdown body)
   - ✉️ Newsletter paragraph (ready to paste into your next issue)
4. Drafts appear in a dark-mode approval queue at `localhost:5050`
5. You click **Approve** or **Dismiss** — nothing goes live without you

## Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/) (Claude Sonnet)
- A GitHub repo where you publish releases

## Setup

```bash
git clone https://github.com/acunningham-ship-it/release-radar
cd release-radar
pip install -r requirements.txt
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY and WEBHOOK_SECRET
```

## Running

```bash
# Start the server
python server.py

# The approval queue is at:
http://localhost:5050/
```

To expose it to GitHub, use [ngrok](https://ngrok.com/download) (free tier works):

```bash
ngrok http 5050
# Copy the HTTPS URL and paste it into your GitHub webhook settings
```

## GitHub webhook setup

1. Go to your repo → **Settings → Webhooks → Add webhook**
2. Payload URL: `https://your-ngrok-url/webhook`
3. Content type: `application/json`
4. Secret: the `WEBHOOK_SECRET` from your `.env`
5. Events: select **Releases** only

## Local test (no webhook needed)

```bash
# While server is running:
python test_local.py
```

This fires `sample_payload.json` at `localhost:5050/webhook` and prints the generated drafts.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Claude API key |
| `WEBHOOK_SECRET` | Recommended | GitHub webhook secret for signature verification |
| `PORT` | No | Server port (default: 5050) |
| `DEBUG` | No | Flask debug mode (default: false) |

## What the output looks like

See [`sample_output.json`](sample_output.json) — this is the actual output from a real test run against `acme/mylib v1.4.0`.

## Production deployment

For always-on hosting, deploy to any free tier that runs Python:
- [Railway](https://railway.app/) — free 500 hours/mo, `Procfile`: `web: python server.py`
- [Fly.io](https://fly.io/) — free tier, `fly launch` then `fly deploy`
- [Render](https://render.com/) — free tier web service

Set your environment variables in the platform dashboard, not in code.

## File structure

```
release-radar/
├── server.py           # Flask webhook + approval queue
├── templates/
│   └── queue.html      # Approval queue UI
├── test_local.py       # End-to-end test script
├── sample_payload.json # Example GitHub release webhook payload
├── sample_output.json  # Real output from test run
├── test_proof.log      # Full end-to-end test log
├── requirements.txt
└── .env.example
```

## License

MIT — use it, modify it, resell the outputs.
