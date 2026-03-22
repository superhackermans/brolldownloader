"""Google Custom Search for images + Playwright for article screenshots."""
from googleapiclient.discovery import build
from config import GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID
import os

_cse = None


def _get_cse():
    global _cse
    if _cse is None:
        _cse = build('customsearch', 'v1', developerKey=GOOGLE_CSE_API_KEY)
    return _cse


def search_images(query: str, max_results: int = 5) -> list[dict]:
    """Search Google for images."""
    try:
        response = _get_cse().cse().list(
            q=query,
            searchType='image',
            num=min(max_results, 10),
            cx=GOOGLE_CSE_ID,
            imgSize='LARGE',
            safe='active'
        ).execute()

        results = []
        for item in response.get('items', []):
            results.append({
                'url': item['link'],
                'title': item.get('title', ''),
                'source': item.get('displayLink', ''),
                'width': item.get('image', {}).get('width', 0),
                'height': item.get('image', {}).get('height', 0),
            })
        return results
    except Exception as e:
        print(f"  Image search error for '{query}': {e}")
        return []


def download_image(url: str, filepath: str) -> bool:
    """Download an image from URL."""
    import requests
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        if response.status_code == 200 and len(response.content) > 5000:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
    except Exception:
        pass
    return False


async def screenshot_article(url: str, filepath: str) -> bool:
    """Screenshot a web article using Playwright."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
            await page.goto(url, timeout=15000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path=filepath, full_page=False)
            await browser.close()
        return os.path.exists(filepath)
    except Exception as e:
        print(f"  Screenshot error for {url}: {e}")
        return False
