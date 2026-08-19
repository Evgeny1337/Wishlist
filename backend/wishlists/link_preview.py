import httpx
from bs4 import BeautifulSoup


def fetch_link_preview(url: str) -> dict[str, str]:
    result = dict(preview_title="", preview_image_url="")
    if not url:
        return result
    try:
        with httpx.Client(timeout=2) as client:
            content =  client.get(url)
            content = content.text
            soup = BeautifulSoup(content, 'html.parser')
            title_tag = soup.find('meta', attrs={'property': 'og:title'})
            image_tag = soup.find('meta', attrs={'property': 'og:image'})
            result["preview_title"] = title_tag.get('content') if title_tag else ""
            result["preview_image_url"] = image_tag.get('content') if image_tag else ""
            return result
    except httpx.HTTPError:
        return result
    except AttributeError:
        return result
