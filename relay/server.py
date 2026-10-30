#!/usr/bin/env python3
"""Team handoff relay: presence, messages and handoffs between Claude Code sessions.

Standard library only. Run it somewhere every teammate can reach:

    TEAM_TOKEN=<host secret> python3 server.py --port 8787 --data relay.json

Every request carries the header `X-Team-Token`. TEAM_TOKEN is the host's admin
token: it invites and removes people. A teammate gets a personal token by
redeeming a one-time invite code, and that token only ever acts as that teammate.
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
INVITE_SECONDS = 600
KINDS = {"handoff", "request", "note", "reply", "connect", "accept", "disconnect", "chat", "ask", "answer", "typing"}
# Codes skip look-alike characters (0/O, 1/I/L) so they can be read out loud.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
# Wrong invite codes allowed per address before it has to wait.
REDEEM_FAILURES = 10
REDEEM_WINDOW = 600

lock = threading.Lock()
db = {"members": {}, "messages": [], "tokens": {}, "invites": {}}
data_path = None
redeem_failures = {}


def load():
    global db
    if data_path and os.path.exists(data_path):
        with open(data_path) as f:
            db = json.load(f)
    for key, empty in (("members", {}), ("messages", []), ("tokens", {}), ("invites", {})):
        db.setdefault(key, empty)


def save():
    if not data_path:
        return
    tmp = data_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(db, f)
    os.replace(tmp, data_path)


def log(line):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), line, flush=True)


def members_view():
    now = time.time()
    return sorted(
        (
            {**m, "online": now - m["lastSeen"] < ONLINE_SECONDS}
            for m in db["members"].values()
        ),
        key=lambda m: (not m["online"], m["user"]),
    )


def new_code():
    raw = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"


def normalize_code(code):
    return "".join(c for c in str(code).upper() if c in CODE_ALPHABET)


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
        """Sets self.admin and self.user from the token, or answers 401."""
        admin_token = os.environ.get("TEAM_TOKEN", "")
        given = self.headers.get("X-Team-Token", "")
        self.admin, self.user = False, None
        if admin_token and secrets.compare_digest(admin_token, given):
            self.admin = True
            return True
        with lock:
            user = db["tokens"].get(given) if given else None
        if user:
            self.user = user
            return True
        log(f"refused: wrong or missing token from {self.client_address[0]}")
        self.reply(401, {"error": "bad or missing X-Team-Token"})
        return False

    def acts_as(self, user):
        """A personal token may only act as its own handle; the host's may act as anyone."""
        if self.admin or self.user == user:
            return True
        log(f"refused: {self.user} tried to act as {user} from {self.client_address[0]}")
        self.reply(403, {"error": f"this token belongs to {self.user}"})
        return False

    def body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        if not self.authorized():
            return
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path == "/members":
            with lock:
                return self.reply(200, {"members": members_view()})
        if url.path == "/inbox":
            user = (query.get("user") or [""])[0].lower()
            if not self.acts_as(user):
                return
            with lock:
                pending = [m for m in db["messages"] if m["to"] == user and not m["acked"]]
            return self.reply(200, {"messages": pending})
        self.reply(404, {"error": "not found"})

    def redeem(self, data):
        """Trades a one-time invite code for a personal token. Needs no token."""
        address = self.client_address[0]
        now = time.time()
        recent = [t for t in redeem_failures.get(address, []) if now - t < REDEEM_WINDOW]
        if len(recent) >= REDEEM_FAILURES:
            return self.reply(429, {"error": "too many wrong codes; wait ten minutes"})
        code = normalize_code(data.get("code", ""))
        invite = db["invites"].pop(code, None)
        if not invite or invite["expires"] < now:
            redeem_failures[address] = recent + [now]
            log(f"refused: unknown or expired invite code from {address}")
            return self.reply(404, {"error": "unknown or expired invite code"})
        token = secrets.token_urlsafe(24)
        db["tokens"][token] = invite["user"]
        save()
        log(f"invite redeemed: {invite['user']} from {address}")
        return self.reply(200, {"user": invite["user"], "token": token})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self.body()
        except json.JSONDecodeError:
            return self.reply(400, {"error": "body is not JSON"})

        if path == "/redeem":
            with lock:
                return self.redeem(data)
        if not self.authorized():
            return

        with lock:
            if path == "/invite" or path == "/remove":
                if not self.admin:
                    return self.reply(403, {"error": "only the host can invite or remove people"})
                user = str(data.get("user", "")).strip().lower()
                if not user:
                    return self.reply(400, {"error": "user is required"})
                if path == "/invite":
                    # One live invite per person: a new one replaces the old.
                    db["invites"] = {c: i for c, i in db["invites"].items() if i["user"] != user}
                    code = new_code()
                    db["invites"][normalize_code(code)] = {"user": user, "expires": time.time() + INVITE_SECONDS}
                    save()
                    log(f"invited: {user}")
                    return self.reply(200, {"user": user, "code": code, "expiresIn": INVITE_SECONDS})
                db["tokens"] = {t: u for t, u in db["tokens"].items() if u != user}
                db["invites"] = {c: i for c, i in db["invites"].items() if i["user"] != user}
                db["members"].pop(user, None)
                save()
                log(f"removed: {user}")
                return self.reply(200, {"ok": True})

            if path == "/presence":
                user = str(data.get("user", "")).lower()
                if not user:
                    return self.reply(400, {"error": "user is required"})
                if not self.acts_as(user):
                    return
                if user not in db["members"]:
                    log(f"joined: {user} from {self.client_address[0]}")
                db["members"][user] = {
                    "user": user,
                    "repo": data.get("repo", ""),
                    "branch": data.get("branch", ""),
                    "status": data.get("status", ""),
                    "version": str(data.get("version", ""))[:20],
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
                if not self.acts_as(sender):
                    return
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
                if not self.acts_as(user):
                    return
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
        raise SystemExit("Set TEAM_TOKEN to the host's secret first.")
    data_path = args.data
    load()
    print(f"team-handoff relay on http://{args.host}:{args.port}", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
