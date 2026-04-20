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
SESSION_COOKIE = "__hssrc=1; intercom-id-mbdwkcq4=0f515112-b39d-4d10-ae3f-026a3c8de0bd; intercom-session-mbdwkcq4=; intercom-device-id-mbdwkcq4=edccf657-c85c-4250-b7dc-1f7f36d1f7be; _vwo_uuid=D0967FB3467DCEF1633BA905C63FEA4DD; cookieyes-consent=consentid:YU5RVmVyZHhlc0E5TXhlUnBsTXNrUzkzNzhKR2drZGU,consent:yes,action:yes,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes; _gcl_au=1.1.924416392.1776627914; _ga=GA1.1.713015112.1776627911; _uetvid=486356603c2811f1af4cd1778868cc22; _vwo_ds=3%3Aa_0%2Ct_0%3A0%241776627910%3A30.05925597%3A%3A%3A%3A3; _fbp=fb.1.1776627913786.677580302360460412; _clck=32jiz1%5E2%5Eg5c%5E0%5E2300; _ga_WFJT5GD144=GS2.1.s1776627910$o1$g0$t1776627915$j58$l0$h0; _pxvid=4a54728c-3c28-11f1-8976-764f1fadfe54; __stripe_mid=41e4ed3b-4a64-41eb-8ef0-1ea5b90efa9f452970; csrf_token=ljFzuekBxcU1FbO/cI2SOjsAWy+vw99UrKHhzdHdlBEn3mKLhDmlgSlLZvrH8q1LDeylQUrnoe/E8zhXnQBcHQ==; mp_7dabee4b82092b66b49e669ddcddd905_mixpanel=%7B%22distinct_id%22%3A%20%22f81525b1-686d-4d54-8418-8f13f5460f80%22%2C%22%24device_id%22%3A%20%2219da7469f9f3a4-0a719c3873dad68-19525631-157188-19da7469fa03a4%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fmybrightwheel.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22mybrightwheel.com%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22appVersion%22%3A%20%224327%22%2C%22releaseTarget%22%3A%20%22stable%22%2C%22%24user_id%22%3A%20%22f81525b1-686d-4d54-8418-8f13f5460f80%22%7D; _px3=9e935cb562afa6b59de5f9c73cdea5ff6e2e046d4411bb6d84bdb406625e5285:OSqT7PoAp/gIHebp/YY7jW3UsQgsBKi7UV97UJSX5ugWDSRLW+5CRigo8JhCQydN3pBg+MmHuzgoDslsVU+AHA==:1000:uk3PjsMKbWTJyd8GNzOK75LiKwSsyDngoFlDd78XSnYi16dn8OkLtgeOlJ1y7TI26jSC1a2vYnDgkhZcTjxm/JsSARQw3F+bqbSGVjjQyS9Zvk0fw5JO5cziwFiywngE6O/HtrxrshXbX8TpHvXN7GMerUC1fVes56e3voR+Fvy2EkMB6X8dopmSALA/9jIct/gjGGwpdS+PE+ZeAzMdS0V2kAj94xsrcqrBKW2zofU80Ju51Tqldg6o8wtbOwaDzXkz3nbNio0tMLxhxN6LjV7e5zeORlnoooj0XBenG3p9w9+zrU0SgjZmBMebDU8rOqq7KHp0v76jLLW/UXDVtYP/YEEA/cT4x7j26vBzolpa+e8zcFJIuIQgzdlHGiVPHQFrje4ia6ePn62hoHlGWDDlPN+HBh3XC1UkghoxLBgNfkoFgKfPVYS6/EyjBFVSbFghIr2LnEWieEqcPsdzhEtA+GHPlvUq6eeAHItHl8l9bLUZn8e7l3ShDg+kYqlZ; pxcts=aTYkGNjuq2nGJ7uGn-ivUcxrjUtFRiEKbnpTVbhGGK0=:i42u5KO3jMBS-89eVA/yEtSr5-BZAmEYAnZmQYAR-XqQNqZFaxslWXvYKqMsLzBKnvux5dm3gZTJkUh-7l3bBK2TBQphWdbxc8a5lBn1RlPy8gichd/WlZbXojdnzOl2furcsD-zabKzfgnuiUblBDbT3C46EpPXhV8pZbFyZGpL1OgZBT9GzPNciq1MoBkX; _brightwheel_v2=K1lmVlJodC9KbXRrVFBGaGt6QlVvQlg5NnN5eVpMRTBweWhoc3MzeXJNS3A2dk1qams1OGR6bUtQc2hMV3NZT3JJbFh1QTBJSDN2QXFGRDU4UXFTRVVhTmVEUzk3OEw3bzdsMGpmZWZuYWJaQnhCRjlncnVPREVNZ2F5RUwwK1pRS0VuQkNabXNjM0RzVU0rMzU3K2hkaGs5c2VScitRdDRXRW1IZ3hDYVh3ay94M0doeXU1TS9yRUp6NExXaityeEJhZnA4NWwwNUwvL1F6MTV2VGdkZ29Hc1JDRlZqaWxIOHc3aWFMeldWL0tyaGlBbDc1bm5peFJITkFQS2Uxa2Z0Q1UxMXkxc1VXeEN6ejJVNkZKSkk1UzR2QWQ0TWdZblpPdENjMy9RZ1A0T05IUXgra2xnc3ExWEsvZDdrekVkSWIwVXpYaWs4SkZtU2JZeW1sN1cxOHBVU2lzU296T3UvQ1RPN3VNWDlreVBBbkExSHRMQWlZU1FXYTI3Umw3MWU5THFnWTBvZnZOQzJPaE52cFlRTjB1bisvM09jcERxc3dvYnl1UFR5Vk0xL240WEI5bi9DMTVUUVNSeHpyeFZZdnZteDB6azdrOU9za2tVQ3k1OEE9PS0tQnFvM1F3dllrbzRTWDY0QmRRSFFUUT09--81be0d5267de3969a91260541ee8680a2add0626"
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

    page = 45
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
