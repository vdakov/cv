#!/usr/bin/env python3
"""
Simple local development server for the multi-page CV website.
Compiles Markdown pages (CV, News, Blog, Photos) with the ModernCV template
and serves them at http://localhost:8000 with instant hot-reload on browser refresh.

Usage:
    ./serve.sh
    python3 serve.py [port]
"""

import csv
import html
import http.server
import os
import re
import socketserver
import sys
import webbrowser
from generate_pdf import convert_markdown_to_html

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

def render_photos_body(repo_dir, md_path):
    """Render photo gallery HTML from CSV data and markdown metadata."""
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    title_match = re.search(r"^title:\s*(.+)$", md_text, re.MULTILINE)
    title = title_match.group(1).strip().strip("'\"") if title_match else "Photography"

    subtitle_match = re.search(r"^subtitle:\s*(.+)$", md_text, re.MULTILINE)
    subtitle = subtitle_match.group(1).strip().strip("'\"") if subtitle_match else ""

    body_md = re.sub(r"^---\n.*?\n---\n?", "", md_text, flags=re.DOTALL).strip()
    intro_html = ""
    if body_md:
        try:
            import tempfile
            with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp:
                tmp.write(body_md)
                tmp_path = tmp.name
            intro_html = f'<div class="photos-intro">{convert_markdown_to_html(tmp_path)}</div>'
            os.remove(tmp_path)
        except Exception:
            intro_html = f'<div class="photos-intro"><p>{html.escape(body_md)}</p></div>'

    csv_path = os.path.join(repo_dir, "_data", "photos.csv")
    if not os.path.isfile(csv_path):
        csv_path = os.path.join(repo_dir, "photos.csv")

    cards_html = []
    if os.path.isfile(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fname = (row.get("filename") or row.get("image") or row.get("file") or "").strip()
                if not fname:
                    continue
                if "/" in fname:
                    img_url = fname
                else:
                    img_url = f"/images/photos/{fname}"

                p_title = (row.get("title") or "").strip()
                p_caption = (row.get("caption") or "").strip()
                p_loc = (row.get("location") or "").strip()
                p_date = (row.get("date") or "").strip()

                meta_parts = []
                if p_loc:
                    meta_parts.append(p_loc)
                if p_date:
                    meta_parts.append(p_date)
                meta_str = " • ".join(meta_parts)

                title_div = f'<div class="overlay-title">{html.escape(p_title)}</div>' if p_title else ""
                caption_div = f'<div class="overlay-caption">{html.escape(p_caption)}</div>' if p_caption else ""
                meta_div = f'<div class="overlay-meta"><span>{html.escape(meta_str)}</span></div>' if meta_str else ""

                cards_html.append(f"""
      <div class="photo-item" tabindex="0" data-full="{html.escape(img_url)}" data-title="{html.escape(p_title)}" data-caption="{html.escape(p_caption)}" data-location="{html.escape(p_loc)}" data-date="{html.escape(p_date)}">
        <img src="{html.escape(img_url)}" alt="{html.escape(p_title or p_caption or 'Photo')}" loading="lazy" />
        <div class="photo-caption-overlay">
          {title_div}
          {caption_div}
          {meta_div}
        </div>
      </div>""")

    grid_content = "\n".join(cards_html)
    subtitle_p = f'<p class="page-subtitle">{html.escape(subtitle)}</p>' if subtitle else ""

    gallery_html = f"""
<div class="photos-container">
  <div class="page-header">
    <h1 class="page-title">{html.escape(title)}</h1>
    {subtitle_p}
  </div>
  {intro_html}
  <div class="photo-grid">
    {grid_content}
  </div>
</div>
"""
    return gallery_html + LIGHTBOX_MODAL_HTML

LIGHTBOX_MODAL_HTML = """
<!-- Lightbox Modal -->
<div id="photo-lightbox" class="photo-lightbox" aria-hidden="true" role="dialog">
  <div class="lightbox-overlay"></div>
  <button class="lightbox-btn lightbox-prev" aria-label="Previous photo">&#10094;</button>
  <button class="lightbox-btn lightbox-next" aria-label="Next photo">&#10095;</button>
  <button class="lightbox-btn lightbox-close" aria-label="Close preview">&times;</button>
  <div class="lightbox-dialog">
    <div class="lightbox-media">
      <img id="lightbox-img" src="" alt="" />
    </div>
    <div class="lightbox-details">
      <h3 id="lightbox-title" class="lightbox-title"></h3>
      <p id="lightbox-caption" class="lightbox-caption"></p>
      <div id="lightbox-meta" class="lightbox-meta"></div>
    </div>
  </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
  const lightbox = document.getElementById('photo-lightbox');
  if (!lightbox) return;

  const overlay = lightbox.querySelector('.lightbox-overlay');
  const closeBtn = lightbox.querySelector('.lightbox-close');
  const prevBtn = lightbox.querySelector('.lightbox-prev');
  const nextBtn = lightbox.querySelector('.lightbox-next');
  const lbImg = document.getElementById('lightbox-img');
  const lbTitle = document.getElementById('lightbox-title');
  const lbCaption = document.getElementById('lightbox-caption');
  const lbMeta = document.getElementById('lightbox-meta');

  const items = Array.from(document.querySelectorAll('.photo-item'));
  let currentIndex = -1;

  function showIndex(idx) {
    if (idx < 0) idx = items.length - 1;
    if (idx >= items.length) idx = 0;
    currentIndex = idx;

    const el = items[idx];
    const fullSrc = el.getAttribute('data-full');
    const title = el.getAttribute('data-title') || '';
    const caption = el.getAttribute('data-caption') || '';
    const location = el.getAttribute('data-location') || '';
    const date = el.getAttribute('data-date') || '';

    lbImg.src = fullSrc;
    lbImg.alt = title || caption || 'Photo';
    lbTitle.textContent = title;
    lbTitle.style.display = title ? 'block' : 'none';
    lbCaption.textContent = caption;
    lbCaption.style.display = caption ? 'block' : 'none';

    let metaParts = [];
    if (location) metaParts.push(location);
    if (date) metaParts.push(date);
    lbMeta.textContent = metaParts.join(' • ');
    lbMeta.style.display = metaParts.length ? 'block' : 'none';
  }

  function openLightbox(idx) {
    showIndex(idx);
    lightbox.classList.add('active');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    lightbox.classList.remove('active');
    lightbox.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    lbImg.src = '';
  }

  items.forEach((item, i) => {
    item.addEventListener('click', () => openLightbox(i));
  });

  if (overlay) overlay.addEventListener('click', closeLightbox);
  if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
  if (prevBtn) prevBtn.addEventListener('click', () => showIndex(currentIndex - 1));
  if (nextBtn) nextBtn.addEventListener('click', () => showIndex(currentIndex + 1));

  document.addEventListener('keydown', (e) => {
    if (!lightbox.classList.contains('active')) return;
    if (e.key === 'Escape') closeLightbox();
    else if (e.key === 'ArrowLeft') showIndex(currentIndex - 1);
    else if (e.key === 'ArrowRight') showIndex(currentIndex + 1);
  });
});
</script>
"""

def render_page(repo_dir, md_file, active_page):
    """Render a markdown page into the complete HTML layout matching GitHub Pages."""
    md_path = os.path.join(repo_dir, md_file)
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    title_match = re.search(r"^title:\s*(.+)$", md_text, re.MULTILINE)
    title = title_match.group(1).strip().strip("'\"") if title_match else "Vasil Dakov"

    if active_page == "photos":
        body_html = render_photos_body(repo_dir, md_path)
    else:
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
    main_cls = ' class="main-photos"' if active_page == "photos" else ""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} | Vasil Dakov</title>
  <link rel="icon" type="image/png" href="/portrait.png">
  <link href="/media/moderncv-screen.css?v=2" type="text/css" rel="stylesheet" media="screen">
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

  <main id="main"{main_cls}>
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
    def do_HEAD(self):
        path = self.path.split("?")[0].rstrip("/")
        if path == "":
            path = "/"
        routes = {"/": ("index.md", "cv"), "/index.html": ("index.md", "cv"), "/cv": ("index.md", "cv"), "/news": ("news.md", "news"), "/blog": ("blog.md", "blog"), "/photos": ("photos.md", "photos")}
        if path in routes:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            return
        return super().do_HEAD()

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
