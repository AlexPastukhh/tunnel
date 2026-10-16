"""Windows integration smoke; starts a temporary local server, never installs P1."""
import http.client
import json
import os
import tempfile
import threading
from http.server import ThreadingHTTPServer

with tempfile.TemporaryDirectory(prefix="observatory-test-") as scratch:
    os.environ["P1_DATA_DIR"] = scratch
    import server

    host_snapshot = server.capture_and_store()
    repo = server.capture_repo()
    assert repo["verified"] and repo["state"] == "UP", repo

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    worker = threading.Thread(target=httpd.serve_forever, daemon=True)
    worker.start()
    try:
        for route in ("/", "/api/snapshot", "/api/history", "/api/repo-status", "/api/repo-history"):
            conn = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=5)
            conn.request("GET", route)
            response = conn.getresponse()
            payload = response.read()
            assert response.status == 200, (route, response.status)
            if route == "/api/repo-status":
                assert json.loads(payload)["state"] == "UP"
            if route == "/":
                assert b'repoStatus' in payload and b'hostStatus' in payload
            print("PASS", route, response.status)
            conn.close()
        print("Host collector:", "UP" if host_snapshot.get("ok") else "UNKNOWN")
        print("Repo collector:", repo["state"], repo["mcp_state"])
    finally:
        httpd.shutdown()
        httpd.server_close()
        worker.join(timeout=3)
