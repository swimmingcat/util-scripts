"""
Download all photos from a Brightwheel student feed.

The session cookie (_brightwheel_v2) expires — if you get 401/403 errors,
copy a fresh cookie value from DevTools and update SESSION_COOKIE below.
"""

import os
import re
import time
import requests

# ── Configure these ───────────────────────────────────────────────────────────

BASE_URL = "https://schools.mybrightwheel.com"
STUDENT_ID = "9f9981b8-052a-4bfe-a046-2851fb71ab13"
API_ENDPOINT = f"{BASE_URL}/api/v1/students/{STUDENT_ID}/activities"

# Paste the full cookie string from DevTools → Request Headers → cookie
SESSION_COOKIE = ""
PHOTOS_DIR = "/Users/luyuzhao/Downloads/brightwheel_photos"
TEST_MODE = False  # set to True to download first 2 pages only

# Fetch all activities from the beginning of time
START_DATE = "2019-01-01T00:00:00.000Z"
END_DATE = "2026-12-31T23:59:59.999Z"
PAGE_SIZE = 50

# ─────────────────────────────────────────────────────────────────────────────

def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Accept": "application/json",
        "Cookie": SESSION_COOKIE,
        "x-api-client-type": "manual",
        "x-client-name": "web",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    })
    return s


def fetch_page(session: requests.Session, page: int) -> dict:
    params = {
        "page": page,
        "page_size": PAGE_SIZE,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "include_parent_actions": "true",
    }
    resp = session.get(API_ENDPOINT, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def extract_photo_urls(data: dict) -> list[str]:
    urls = []
    for item in data.get("activities", []):
        if item.get("action_type") != "ac_photo":
            continue
        url = item.get("media", {}).get("image_url")
        if url:
            urls.append(url)
    return urls


def has_more_pages(data: dict, page: int) -> bool:
    total = data.get("count", 0)
    return (page + 1) * PAGE_SIZE < total


def filename_from_url(url: str, index: int) -> str:
    # Strip query string, then split on both "/" and "%2F" (encoded slash)
    path = url.split("?")[0]
    name = re.split(r"/|%2F", path, flags=re.I)[-1]
    if not re.search(r"\.(jpe?g|png|gif|webp)$", name, re.I):
        name = f"photo_{index:04d}.jpg"
    return name


def download_photo(session: requests.Session, url: str, dest: str) -> None:
    resp = session.get(url, timeout=60, stream=True)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


def main():
    if not SESSION_COOKIE:
        raise SystemExit("Set SESSION_COOKIE before running.")

    os.makedirs(PHOTOS_DIR, exist_ok=True)
    session = build_session()

    page = 0
    total_downloaded = 0
    photo_index = 0

    while True:
        print(f"\nPage {page}...")
        data = fetch_page(session, page)
        urls = extract_photo_urls(data)
        print(f"  {len(urls)} photos found")

        for url in urls:
            photo_index += 1
            filename = filename_from_url(url, photo_index)
            dest = os.path.join(PHOTOS_DIR, filename)

            if os.path.exists(dest):
                print(f"  Skip (exists): {filename}")
                continue

            try:
                download_photo(session, url, dest)
                total_downloaded += 1
                print(f"  Downloaded: {filename}")
            except Exception as e:
                print(f"  FAILED {filename}: {e}")

            time.sleep(0.1)

        if not has_more_pages(data, page) or (TEST_MODE and page >= 1):
            break
        page += 1
        time.sleep(0.3)

    print(f"\nDone. {total_downloaded} new photos saved to {PHOTOS_DIR}/")


if __name__ == "__main__":
    main()
