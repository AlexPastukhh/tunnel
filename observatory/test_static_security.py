"""Prove static server cannot read outside public assets.

All files are synthetic in TemporaryDirectory. Do not access real owner files.
"""
import http.client
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch

import server


class StaticSecurityTests(unittest.TestCase):
    def test_only_exact_html_js_css_get_and_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "public"
            root.mkdir()
            (root / "index.html").write_text("FAKE_PUBLIC_HTML", encoding="utf-8")
            (root / "styles.css").write_text("FAKE_PUBLIC_CSS", encoding="utf-8")
            (root / "app.js").write_text("FAKE_PUBLIC_JS", encoding="utf-8")
            (root / "data").mkdir()
            (root / "data" / "private.db").write_text("FAKE_PRIVATE_ARCHIVE", encoding="utf-8")
            (root / "server.py").write_text("FAKE_PRIVATE_SOURCE", encoding="utf-8")
            (Path(tmp) / "owner_secret.txt").write_text("FAKE_OWNER_SECRET", encoding="utf-8")

            with patch.object(server, "ROOT", root):
                httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
                thread = Thread(target=httpd.serve_forever, daemon=True)
                thread.start()
                try:
                    client = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=3)
                    for path in ("/", "/index.html", "/app.js", "/styles.css"):
                        client.request("GET", path)
                        response = client.getresponse()
                        response.read()
                        self.assertEqual(response.status, 200, path)
                        client.request("HEAD", path)
                        response = client.getresponse()
                        response.read()
                        self.assertEqual(response.status, 200, path)

                    # These used to be returned by inherited SimpleHTTPRequestHandler.
                    for path in ("/../owner_secret.txt", "/data/private.db",
                                 "/server.py", "/../public/data/private.db",
                                 "/%2e%2e/owner_secret.txt"):
                        for method in ("GET", "HEAD"):
                            client.request(method, path)
                            response = client.getresponse()
                            body = response.read()
                            self.assertEqual(response.status, 404, (method, path))
                            self.assertNotIn(b"FAKE_PRIVATE", body)
                            self.assertNotIn(b"FAKE_OWNER_SECRET", body)
                    client.request("GET", "/?unsafe=1/../owner_secret.txt")
                    query = client.getresponse()
                    body = query.read()
                    self.assertEqual(query.status, 200)  # "/" with a query still serves index
                    self.assertNotIn(b"FAKE_OWNER_SECRET", body)
                    client.close()
                finally:
                    httpd.shutdown()
                    httpd.server_close()
                    thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
