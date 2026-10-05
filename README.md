## Vasil Dakov — Personal Website & CV

Personal website and curriculum vitae built with Markdown, ModernCV styling, Jekyll, and HTML/CSS.

### Site Structure
- **CV**: Main curriculum vitae (`index.md`, served at `/` and `/cv/`)
- **News**: Career milestones, awards, and professional timeline (`news.md`, served at `/news/`)
- **Blog**: Technical articles and research write-ups (`blog.md`, served at `/blog/`)
- **Photos**: Photography showcase across travel and street perspectives (`photos.md`, served at `/photos/`)

### Photography Gallery & CSV Captions

To add or update photos in the gallery:
1. **Drop pictures** into the `images/photos/` directory (e.g. `images/photos/my-photo.jpg`).
2. **Add rows** to `_data/photos.csv` (or `photos.csv`):
   ```csv
   filename,title,caption,location,date
   sunset-field.jpg,Fiery Countryside Sunset,Vibrant orange and red glow over a quiet countryside garden at dusk.,Bulgaria,Aug 2026
   ```
   - `filename`: Image filename in `images/photos/` (required)
   - `title`: Short photo title (optional)
   - `caption`: Caption / description (optional)
   - `location`: Location name (optional)
   - `date`: Month / year or season (optional)
3. **Preview locally** with `./serve.sh` and push to publish automatically on GitHub Pages. Clicking any card opens a high-resolution lightbox modal with full details.

### Export to PDF

To generate the clean, 2-page ModernCV PDF:
```bash
./generate_pdf.sh
```
or specify a custom output filename:
```bash
./generate_pdf.sh Vasil_Dakov_CV.pdf
```
This converts the Markdown content and prints using Chrome headless into an exact two-page PDF.

### Run Locally

**Option 1: Instant Python Preview (Zero dependencies)**
```bash
./serve.sh
```
Opens `http://localhost:8000` with live re-rendering on page refresh across all pages (`/`, `/news/`, `/blog/`, `/photos/`).

**Option 2: Jekyll (Standard GitHub Pages)**
```bash
bundle install
bundle exec jekyll serve
```
Opens `http://localhost:4000`.

### License

[MIT License](https://github.com/elipapa/markdown-cv/blob/master/LICENSE)
