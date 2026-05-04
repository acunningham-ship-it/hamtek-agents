#!/usr/bin/env bash
# Run end-to-end test using the claude CLI for auth (dev/demo use only)
# Production use: set ANTHROPIC_API_KEY in .env
set -e

cd "$(dirname "$0")"

# Extract API key from claude CLI config
ANTHROPIC_API_KEY=$(python3 -c "
import json, os
cfg = os.path.expanduser('~/.claude.json')
d = json.load(open(cfg))
# Try oauthAccount token first, then apiKey
token = d.get('oauthAccount', {}).get('accessToken') or d.get('apiKey', '')
print(token)
" 2>/dev/null || echo "")

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "No ANTHROPIC_API_KEY found. Set it in .env or log in with claude."
  exit 1
fi

export ANTHROPIC_API_KEY
export PORT=5051
export DEBUG=true

echo "Starting server on port $PORT..."
python3 server.py &
SERVER_PID=$!
sleep 2

echo "Running test..."
python3 test_local.py --url "http://localhost:$PORT"
TEST_EXIT=$?

kill $SERVER_PID 2>/dev/null || true
exit $TEST_EXIT
