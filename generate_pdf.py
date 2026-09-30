#!/usr/bin/env python3
"""
Convert Markdown CV to a PDF using Pandoc/Python and Headless Chrome.

Usage:
    python3 generate_pdf.py [options] [output_file]
    ./generate_pdf.sh [options] [output_file]

Examples:
    python3 generate_pdf.py
    python3 generate_pdf.py Vasil_Dakov_CV.pdf
    python3 generate_pdf.py --keep-html
"""

import argparse
import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile

def find_browser(custom_path=None):
    """Locate a Chromium-based browser capable of headless PDF generation."""
    if custom_path:
        if os.path.isfile(custom_path) and os.access(custom_path, os.X_OK):
            return custom_path
        sys.exit(f"Error: Specified browser not found or not executable: {custom_path}")

    # Standard browser locations on macOS
    macos_candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        os.path.expanduser("~/Applications/Chromium.app/Contents/MacOS/Chromium"),
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        os.path.expanduser("~/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
    ]

    for candidate in macos_candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    # Standard CLI commands (Linux, PATH, etc.)
    cli_candidates = [
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "brave-browser",
        "msedge",
    ]

    for candidate in cli_candidates:
        path = shutil.which(candidate)
        if path:
            return path

    return None

def convert_markdown_to_html(md_path):
    """Convert Markdown file to HTML body using pandoc or python-markdown."""
    # 1. Try Pandoc with GitHub Flavored Markdown
    if shutil.which("pandoc"):
        try:
            result = subprocess.run(
                ["pandoc", md_path, "-f", "gfm", "-t", "html"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Warning: Pandoc failed ({e.stderr.strip()}), attempting fallbacks...", file=sys.stderr)

    # 2. Try Python markdown module
    try:
        import markdown
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        # Strip YAML frontmatter if present
        md_content = re.sub(r"^---\n.*?\n---\n", "", md_content, flags=re.DOTALL)
        return markdown.markdown(md_content, extensions=["extra"])
    except ImportError:
        pass

    # 3. Try uv run --with markdown
    uv_path = shutil.which("uv") or os.path.expanduser("~/.local/bin/uv")
    if os.path.isfile(uv_path) and os.access(uv_path, os.X_OK):
        try:
            script = """
import sys, re, markdown
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    text = f.read()
text = re.sub(r'^---\\n.*?\\n---\\n', '', text, flags=re.DOTALL)
print(markdown.markdown(text, extensions=['extra']))
"""
            result = subprocess.run(
                [uv_path, "run", "--with", "markdown", "python3", "-c", script, md_path],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            pass

    sys.exit("Error: Could not find pandoc, python 'markdown' package, or 'uv'. Please install pandoc or python-markdown.")

def extract_title_and_style(base_dir, md_path):
    """Extract page title and Jekyll style setting."""
    title = "CV"
    style = "kjhealy"

    if os.path.isfile(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
            if match:
                title = match.group(1).strip().strip("'\"")

    config_path = os.path.join(base_dir, "_config.yml")
    if os.path.isfile(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"^style:\s*(.+)$", content, re.MULTILINE)
            if match:
                style = match.group(1).strip().strip("'\"")

    return title, style

def build_full_html(base_dir, md_path):
    """Build a standalone, self-contained HTML document with inlined styles and images."""
    title, style = extract_title_and_style(base_dir, md_path)
    body_html = convert_markdown_to_html(md_path)

    screen_css_path = os.path.join(base_dir, "media", f"{style}-screen.css")
    print_css_path = os.path.join(base_dir, "media", f"{style}-print.css")

    screen_css = ""
    if os.path.isfile(screen_css_path):
        with open(screen_css_path, "r", encoding="utf-8") as f:
            screen_css = f.read()

    print_css = ""
    if os.path.isfile(print_css_path):
        with open(print_css_path, "r", encoding="utf-8") as f:
            print_css = f.read()

    # Favicon base64 embedding if available
    portrait_path = os.path.join(base_dir, "portrait.png")
    favicon_tag = ""
    if os.path.isfile(portrait_path):
        with open(portrait_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("ascii")
            favicon_tag = f'<link rel="icon" type="image/png" href="data:image/png;base64,{b64_data}">'

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{title} | CV</title>
  {favicon_tag}
  <style>
    @media screen {{
{screen_css}
    }}
    @media print {{
{print_css}
    }}
  </style>
</head>
<body>
  <div id="main">
    <div id="content">
{body_html}
    </div>
  </div>
</body>
</html>
"""
    return html

def main():
    parser = argparse.ArgumentParser(description="Convert Markdown CV to a high-quality PDF.")
    parser.add_argument(
        "output",
        nargs="?",
        default="cv.pdf",
        help="Output PDF filename (default: cv.pdf)",
    )
    parser.add_argument(
        "--input",
        "-i",
        default="index.md",
        help="Input Markdown file (default: index.md)",
    )
    parser.add_argument(
        "--browser",
        "-b",
        default=None,
        help="Path to Chrome/Chromium executable",
    )
    parser.add_argument(
        "--keep-html",
        action="store_true",
        help="Keep generated HTML file instead of deleting temporary file",
    )

    args = parser.parse_args()

    repo_dir = os.path.abspath(os.path.dirname(__file__))
    md_path = os.path.join(repo_dir, args.input)
    output_pdf = os.path.abspath(args.output)

    if not os.path.isfile(md_path):
        sys.exit(f"Error: Markdown input file not found: {md_path}")

    browser_bin = find_browser(args.browser)
    if not browser_bin:
        sys.exit(
            "Error: No Chromium-based browser (Google Chrome, Chromium, Brave, Edge) found.\n"
            "Please install Google Chrome or pass the browser path with --browser."
        )

    print(f"📄 Rendering {args.input}...")
    full_html = build_full_html(repo_dir, md_path)

    if args.keep_html:
        html_out_path = os.path.splitext(output_pdf)[0] + ".html"
        with open(html_out_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        temp_html = html_out_path
        cleanup_temp = False
        print(f"📝 Preserved HTML at: {html_out_path}")
    else:
        fd, temp_html = tempfile.mkstemp(suffix=".html", prefix="cv_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(full_html)
        cleanup_temp = True

    try:
        print(f"🌐 Converting to PDF using: {os.path.basename(browser_bin)}...")
        cmd = [
            browser_bin,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={output_pdf}",
            temp_html,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 and not os.path.isfile(output_pdf):
            sys.exit(f"Error executing browser command: {proc.stderr}")

        if os.path.isfile(output_pdf):
            size_kb = os.path.getsize(output_pdf) / 1024.0
            print(f"✅ Successfully generated PDF: {output_pdf} ({size_kb:.1f} KB)")
        else:
            sys.exit("Error: PDF output file was not generated.")
    finally:
        if cleanup_temp and os.path.exists(temp_html):
            os.remove(temp_html)

if __name__ == "__main__":
    main()
