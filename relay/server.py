#!/usr/bin/env python3
"""Team handoff relay: presence, messages and handoffs between Claude Code sessions.

Standard library only. Run it somewhere every teammate can reach:

    TEAM_TOKEN=<shared secret> python3 server.py --port 8787 --data relay.json

Every request must carry the header `X-Team-Token: <shared secret>`.
"""

import argparse
import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ONLINE_SECONDS = 90
KINDS = {"handoff", "request", "note", "reply", "connect", "accept", "disconnect", "chat", "ask", "answer", "typing"}

lock = threading.Lock()
db = {"members": {}, "messages": []}
data_path = None


def load():
    global db
    if data_path and os.path.exists(data_path):
        with open(data_path) as f:
            db = json.load(f)


def save():
    if not data_path:
        return
    tmp = data_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(db, f)
    os.replace(tmp, data_path)


def members_view():
    now = time.time()
    return sorted(
        (
            {**m, "online": now - m["lastSeen"] < ONLINE_SECONDS}
            for m in db["members"].values()
        ),
        key=lambda m: (not m["online"], m["user"]),
    )


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def reply(self, status, body):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def authorized(self):
        token = os.environ.get("TEAM_TOKEN", "")
        given = self.headers.get("X-Team-Token", "")
        if token and secrets.compare_digest(token, given):
            return True
        self.reply(401, {"error": "bad or missing X-Team-Token"})
        return False

    def body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        if not self.authorized():
            return
        url = urlparse(self.path)
        query = parse_qs(url.query)
        with lock:
            if url.path == "/members":
                return self.reply(200, {"members": members_view()})
            if url.path == "/inbox":
                user = (query.get("user") or [""])[0].lower()
                pending = [
                    m for m in db["messages"] if m["to"] == user and not m["acked"]
                ]
                return self.reply(200, {"messages": pending})
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        if not self.authorized():
            return
        path = urlparse(self.path).path
        try:
            data = self.body()
        except json.JSONDecodeError:
            return self.reply(400, {"error": "body is not JSON"})

        with lock:
            if path == "/presence":
                user = str(data.get("user", "")).lower()
                if not user:
                    return self.reply(400, {"error": "user is required"})
                db["members"][user] = {
                    "user": user,
                    "repo": data.get("repo", ""),
                    "branch": data.get("branch", ""),
                    "status": data.get("status", ""),
                    "lastSeen": time.time(),
                }
                save()
                return self.reply(200, {"ok": True})

            if path == "/messages":
                kind = data.get("kind")
                sender = str(data.get("from", "")).lower()
                to = str(data.get("to", "")).lower()
                if kind not in KINDS or not sender or not to:
                    return self.reply(400, {"error": "need kind, from and to"})
                message = {
                    "id": secrets.token_hex(6),
                    "kind": kind,
                    "from": sender,
                    "to": to,
                    "title": str(data.get("title", ""))[:200],
                    "body": str(data.get("body", ""))[:20000],
                    "replyTo": data.get("replyTo"),
                    "group": data.get("group"),
                    "createdAt": time.time(),
                    "acked": False,
                }
                db["messages"].append(message)
                db["messages"] = db["messages"][-2000:]
                save()
                known = to in db["members"]
                return self.reply(200, {"id": message["id"], "knownRecipient": known})

            if path == "/ack":
                ids = set(data.get("ids") or [data.get("id")])
                user = str(data.get("user", "")).lower()
                for m in db["messages"]:
                    if m["id"] in ids and m["to"] == user:
                        m["acked"] = True
                save()
                return self.reply(200, {"ok": True})

        self.reply(404, {"error": "not found"})


def main():
    global data_path
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--data", default="relay.json")
    args = parser.parse_args()
    if not os.environ.get("TEAM_TOKEN"):
        raise SystemExit("Set TEAM_TOKEN to the team's shared secret first.")
    data_path = args.data
    load()
    print(f"team-handoff relay on http://{args.host}:{args.port}")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
