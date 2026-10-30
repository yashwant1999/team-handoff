#!/usr/bin/env bash
# Sets up team-handoff for one teammate. No prompts, so it runs from Claude Code's `!`.
#
#   ./setup.sh --host <your-handle>          start (or restart) the relay here and join it
#   ./setup.sh <your-handle> <url> <token>   join a teammate's relay
#   ./setup.sh --stop                        stop the relay this machine hosts
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
config="$HOME/.config/team-handoff.json"
can_host=false
data="$HOME/.local/share/team-handoff"
port="${PORT:-8787}"

stop_relay() {
  if [[ -f "$data/relay.pid" ]] && kill "$(cat "$data/relay.pid")" 2>/dev/null; then
    echo "Stopped the old relay (pid $(cat "$data/relay.pid"))."
    sleep 1
  fi
  rm -f "$data/relay.pid"
}

usage() {
  sed -n '4,6p' "$0" | sed 's/^# //'
  exit 1
}

case "${1:-}" in
  --stop)
    stop_relay
    exit 0
    ;;
  --host)
    [[ $# -eq 2 ]] || usage
    can_host=true
    user="$2"
    url="http://localhost:$port"
    mkdir -p "$data"
    umask 077
    # Keep one token per host, so teammates' configs survive a restart.
    [[ -s "$data/token" ]] || python3 -c 'import secrets; print(secrets.token_urlsafe(24))' >"$data/token"
    token="$(cat "$data/token")"
    stop_relay
    detach=""; command -v setsid >/dev/null && detach="setsid"
    TEAM_TOKEN="$token" $detach nohup python3 "$here/relay/server.py" --port "$port" \
      --data "$data/relay.json" >"$data/relay.log" 2>&1 &
    echo "$!" >"$data/relay.pid"
    sleep 1
    if ! kill -0 "$(cat "$data/relay.pid")" 2>/dev/null; then
      echo "✗ The relay did not start. Last lines of $data/relay.log:"
      tail -3 "$data/relay.log"
      echo "Port $port busy? Free it, or run with PORT=8788."
      exit 1
    fi
    # `hostname -I` is missing on some distros; ask the routing table instead.
    ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i < NF; i++) if ($i == "src") print $(i + 1)}')" || true
    echo "Relay running on port $port (pid $(cat "$data/relay.pid"), log $data/relay.log)."
    echo "Teammates install the plugin, then type in Claude Code:"
    echo "  /team-join <their-handle> http://${ip:-<this-machine-ip>}:$port $token"
    ;;
  *)
    [[ $# -eq 3 ]] || usage
    user="$1" url="$2" token="$3"
    ;;
esac

mkdir -p "$(dirname "$config")"
umask 077
python3 - "$config" "$user" "$url" "$token" "$can_host" <<'EOF'
import json, sys
path, user, url, token, can_host = sys.argv[1:]
json.dump({"user": user.strip().lower(), "relayUrl": url.rstrip("/"), "teamToken": token,
           "canHost": can_host == "true"},
          open(path, "w"), indent=2)
EOF

if curl -fsS -H "X-Team-Token: $token" "$url/members" >/dev/null 2>&1; then
  echo "✓ Reached the relay at $url as '$user'."
else
  echo "✗ Could not reach $url with that token; check the URL, the token and the network."
  exit 1
fi
echo "Saved $config. In Claude Code, run /team."
