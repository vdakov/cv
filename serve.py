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

                meta_html = ""
                if p_loc or p_date:
                    loc_html = f'<span class="photo-location"><svg class="photo-meta-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> {html.escape(p_loc)}</span>' if p_loc else ""
                    date_html = f'<span class="photo-date"><svg class="photo-meta-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg> {html.escape(p_date)}</span>' if p_date else ""
                    meta_html = f'<div class="photo-meta">{loc_html}{date_html}</div>'

                title_div = f'<div class="photo-title">{html.escape(p_title)}</div>' if p_title else ""
                caption_p = f'<p class="photo-caption">{html.escape(p_caption)}</p>' if p_caption else ""

                cards_html.append(f"""
      <figure class="photo-card" data-full="{html.escape(img_url)}" data-title="{html.escape(p_title)}" data-caption="{html.escape(p_caption)}" data-location="{html.escape(p_loc)}" data-date="{html.escape(p_date)}">
        <div class="photo-img-wrapper">
          <img src="{html.escape(img_url)}" alt="{html.escape(p_title or p_caption or 'Photo')}" loading="lazy" class="photo-img" />
          <div class="photo-overlay">
            <span class="photo-zoom-icon">&#x26F6;</span>
          </div>
        </div>
        <figcaption class="photo-info">
          {title_div}
          {caption_p}
          {meta_html}
        </figcaption>
      </figure>""")

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
<!-- Photo Lightbox Modal -->
<div id="photo-lightbox" class="photo-lightbox" aria-hidden="true" role="dialog">
  <div class="lightbox-overlay"></div>
  <div class="lightbox-dialog">
    <button class="lightbox-close" aria-label="Close photo preview">&times;</button>
    <div class="lightbox-media">
      <img id="lightbox-img" src="" alt="" />
    </div>
    <div class="lightbox-details">
      <h3 id="lightbox-title" class="lightbox-title"></h3>
      <p id="lightbox-caption" class="lightbox-caption"></p>
      <div id="lightbox-meta" class="photo-meta"></div>
    </div>
  </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
  const lightbox = document.getElementById('photo-lightbox');
  if (!lightbox) return;
  const overlay = lightbox.querySelector('.lightbox-overlay');
  const closeBtn = lightbox.querySelector('.lightbox-close');
  const lbImg = document.getElementById('lightbox-img');
  const lbTitle = document.getElementById('lightbox-title');
  const lbCaption = document.getElementById('lightbox-caption');
  const lbMeta = document.getElementById('lightbox-meta');

  function openLightbox(card) {
    const fullSrc = card.getAttribute('data-full');
    const title = card.getAttribute('data-title') || '';
    const caption = card.getAttribute('data-caption') || '';
    const location = card.getAttribute('data-location') || '';
    const date = card.getAttribute('data-date') || '';

    lbImg.src = fullSrc;
    lbImg.alt = title || caption || 'Photo';

    if (title) {
      lbTitle.textContent = title;
      lbTitle.style.display = 'block';
    } else {
      lbTitle.style.display = 'none';
    }

    if (caption) {
      lbCaption.textContent = caption;
      lbCaption.style.display = 'block';
    } else {
      lbCaption.style.display = 'none';
    }

    lbMeta.innerHTML = '';
    if (location) {
      const locSpan = document.createElement('span');
      locSpan.className = 'photo-location';
      locSpan.innerHTML = '<svg class="photo-meta-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> ' + location;
      lbMeta.appendChild(locSpan);
    }
    if (date) {
      const dateSpan = document.createElement('span');
      dateSpan.className = 'photo-date';
      dateSpan.innerHTML = '<svg class="photo-meta-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg> ' + date;
      lbMeta.appendChild(dateSpan);
    }

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

  document.querySelectorAll('.photo-card').forEach(function(card) {
    card.addEventListener('click', function() {
      openLightbox(card);
    });
  });

  if (overlay) overlay.addEventListener('click', closeLightbox);
  if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && lightbox.classList.contains('active')) {
      closeLightbox();
    }
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
