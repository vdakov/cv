#!/usr/bin/env python3
"""
Simple local development server for the multi-page CV website.
Compiles Markdown pages (CV, News, Blog, Photos) with the ModernCV template
and serves them at http://localhost:8000 with instant hot-reload on browser refresh.

Usage:
    ./serve.sh
    python3 serve.py [port]
"""

import http.server
import os
import re
import socketserver
import sys
import webbrowser
from generate_pdf import convert_markdown_to_html

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

def render_page(repo_dir, md_file, active_page):
    """Render a markdown page into the complete HTML layout matching GitHub Pages."""
    md_path = os.path.join(repo_dir, md_file)
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    title_match = re.search(r"^title:\s*(.+)$", md_text, re.MULTILINE)
    title = title_match.group(1).strip().strip("'\"") if title_match else "Vasil Dakov"

    body_html = convert_markdown_to_html(md_path)

    # In local server, strip relative_url Liquid tags if any made it through raw HTML
    body_html = body_html.replace("{{ '/' | relative_url }}", "/")

    nav_items = [
        ("cv", "/", "CV"),
        ("news", "/news/", "News"),
        ("blog", "/blog/", "Blog"),
        ("photos", "/photos/", "Photos"),
    ]

    nav_links_html = []
    for page_key, path, label in nav_items:
        active_cls = " active" if active_page == page_key else ""
        nav_links_html.append(f'<a href="{path}" class="nav-link{active_cls}">{label}</a>')
    nav_links_html.append('<a href="/cv.pdf" class="nav-link nav-pdf-btn" download>PDF &darr;</a>')
    nav_links_str = "\n        ".join(nav_links_html)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} | Vasil Dakov</title>
  <link rel="icon" type="image/png" href="/portrait.png">
  <link href="/media/moderncv-screen.css" type="text/css" rel="stylesheet" media="screen">
  <link href="/media/moderncv-print.css" type="text/css" rel="stylesheet" media="print">
</head>
<body>
  <header class="site-header no-print">
    <div class="site-nav-container">
      <a class="site-brand" href="/">vdakov.github.io</a>
      <nav class="site-nav">
        {nav_links_str}
      </nav>
    </div>
  </header>

  <main id="main">
    <div id="content">
      {body_html}
    </div>
  </main>

  <footer class="site-footer no-print">
    <div class="footer-container">
      <span>&copy; 2026 Vasil Dakov</span>
      <span>
        <a href="mailto:v.dakov02@gmail.com">Email</a> &bull;
        <a href="https://github.com/vdakov" target="_blank" rel="noopener">GitHub</a> &bull;
        <a href="https://www.linkedin.com/in/vasil-dakov-727506230/" target="_blank" rel="noopener">LinkedIn</a> &bull;
        <a href="https://scholar.google.com/citations?user=Chi1QkQAAAAJ&hl=en" target="_blank" rel="noopener">Google Scholar</a>
      </span>
    </div>
  </footer>
</body>
</html>"""

class CVHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Normalize request path
        path = self.path.split("?")[0].rstrip("/")
        if path == "":
            path = "/"

        routes = {
            "/": ("index.md", "cv"),
            "/index.html": ("index.md", "cv"),
            "/cv": ("index.md", "cv"),
            "/news": ("news.md", "news"),
            "/blog": ("blog.md", "blog"),
            "/photos": ("photos.md", "photos"),
        }

        if path in routes:
            md_file, active_page = routes[path]
            repo_dir = os.path.abspath(os.path.dirname(__file__))
            try:
                html = render_page(repo_dir, md_file, active_page)
                encoded = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
                return
            except Exception as e:
                self.send_error(500, f"Error compiling markdown {md_file}: {e}")
                return

        return super().do_GET()

def main():
    repo_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(repo_dir)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CVHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"🚀 CV local server running at: {url}")
        print("📁 Available routes:")
        print(f"   • CV:     {url}/")
        print(f"   • News:   {url}/news/")
        print(f"   • Blog:   {url}/blog/")
        print(f"   • Photos: {url}/photos/")
        print("💡 Edits to any .md or media/*.css will update on browser refresh!")
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
