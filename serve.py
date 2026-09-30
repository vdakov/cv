#!/usr/bin/env python3
"""
Simple local development server for the CV website.
Compiles index.md with the Jekyll template and serves it at http://localhost:8000.

Usage:
    ./serve.sh
    python3 serve.py [port]
"""

import http.server
import os
import socketserver
import sys
import webbrowser
from generate_pdf import build_full_html

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

class CVHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Dynamically re-render index.md on every refresh so edits appear instantly!
        if self.path in ("/", "/index.html"):
            repo_dir = os.path.abspath(os.path.dirname(__file__))
            md_path = os.path.join(repo_dir, "index.md")
            try:
                html = build_full_html(repo_dir, md_path)
                encoded = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
                return
            except Exception as e:
                self.send_error(500, f"Error compiling markdown: {e}")
                return

        return super().do_GET()

def main():
    repo_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(repo_dir)

    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CVHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"🚀 CV local server running at: {url}")
        print("💡 Edits to index.md and media/*.css will update on refresh!")
        print("Press Ctrl+C to stop.")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped.")

if __name__ == "__main__":
    main()
