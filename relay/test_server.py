"""Runs the relay on a free port and checks invites, personal tokens and the host's rights.

    python3 relay/test_server.py
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ADMIN = "host-secret"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class RelayTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.port = free_port()
        self.proc = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "server.py"), "--host", "127.0.0.1",
             "--port", str(self.port), "--data", os.path.join(self.dir.name, "relay.json")],
            env={**os.environ, "TEAM_TOKEN": ADMIN},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=0.1).close()
                break
            except OSError:
                time.sleep(0.05)

    def tearDown(self):
        self.proc.terminate()
        self.proc.wait()
        self.dir.cleanup()

    def call(self, path, body=None, token=None):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=None if body is None else json.dumps(body).encode(),
            headers={"Content-Type": "application/json", **({"X-Team-Token": token} if token else {})},
            method="GET" if body is None else "POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    def invite(self, user):
        status, body = self.call("/invite", {"user": user}, ADMIN)
        self.assertEqual(status, 200)
        return body["code"]

    def test_an_invite_code_becomes_a_personal_token_once(self):
        code = self.invite("vatsal")
        status, body = self.call("/redeem", {"code": code.lower().replace("-", " ")})
        self.assertEqual((status, body["user"]), (200, "vatsal"))
        self.assertEqual(self.call("/presence", {"user": "vatsal"}, body["token"])[0], 200)
        self.assertEqual(self.call("/redeem", {"code": code})[0], 404)

    def test_a_personal_token_cannot_act_as_someone_else(self):
        _, body = self.call("/redeem", {"code": self.invite("vatsal")})
        token = body["token"]
        self.assertEqual(self.call("/presence", {"user": "yash"}, token)[0], 403)
        self.assertEqual(self.call("/messages", {"kind": "chat", "from": "yash", "to": "sam"}, token)[0], 403)
        self.assertEqual(self.call("/inbox?user=yash", token=token)[0], 403)
        self.assertEqual(self.call("/messages", {"kind": "chat", "from": "vatsal", "to": "yash"}, token)[0], 200)

    def test_only_the_host_invites_and_removes(self):
        _, body = self.call("/redeem", {"code": self.invite("vatsal")})
        token = body["token"]
        self.assertEqual(self.call("/invite", {"user": "sam"}, token)[0], 403)
        self.assertEqual(self.call("/remove", {"user": "vatsal"}, ADMIN)[0], 200)
        self.assertEqual(self.call("/members", token=token)[0], 401)

    def test_wrong_codes_are_limited(self):
        for _ in range(10):
            self.assertEqual(self.call("/redeem", {"code": "AAAA-AAAA"})[0], 404)
        self.assertEqual(self.call("/redeem", {"code": self.invite("vatsal")})[0], 429)


if __name__ == "__main__":
    unittest.main()
