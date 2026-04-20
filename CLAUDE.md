# util-scripts

A collection of Python utility scripts.

## Setup

```bash
uv sync
```

## Scripts

### download_brightwheel_photos.py

Downloads all photos from a Brightwheel student feed.

**Configuration** (edit at top of file):
- `SESSION_COOKIE` — paste the full cookie string from DevTools → Network → any `/activities` request → Request Headers → `cookie`. Expires periodically; refresh if you get 401/403.
- `STUDENT_ID` — the student UUID from the feed URL
- `PHOTOS_DIR` — local path to save photos (created automatically)
- `TEST_MODE = True` — limits to first 2 pages for testing

**Run:**
```bash
uv run download_brightwheel_photos.py
```

**How it works:**
- Calls `GET /api/v1/students/{id}/activities` with pagination (`page`, `page_size`)
- Filters activities where `action_type == "ac_photo"`
- Extracts `media.image_url` (signed CloudFront URL)
- Fetches and downloads each page's photos immediately (before signed URLs expire)
- Skips already-downloaded files
