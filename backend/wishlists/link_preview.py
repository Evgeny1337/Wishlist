import httpx
from bs4 import BeautifulSoup

PREVIEW_TITLE_MAX_LENGTH = 200
PREVIEW_IMAGE_URL_MAX_LENGTH = 1000


def _as_text(value: object, max_length: int) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) <= max_length:
        return text
    return text[:max_length]


def fetch_link_preview(url: str) -> dict[str, str]:
    result = dict(preview_title="", preview_image_url="")
    if not url:
        return result
    try:
        with httpx.Client(timeout=2, follow_redirects=True) as client:
            content = client.get(url)
            content = content.text
            soup = BeautifulSoup(content, "html.parser")
            title_tag = soup.find("meta", attrs={"property": "og:title"})
            image_tag = soup.find("meta", attrs={"property": "og:image"})
            result["preview_title"] = _as_text(
                title_tag.get("content") if title_tag else "",
                PREVIEW_TITLE_MAX_LENGTH,
            )
            result["preview_image_url"] = _as_text(
                image_tag.get("content") if image_tag else "",
                PREVIEW_IMAGE_URL_MAX_LENGTH,
            )
            return result
    except httpx.HTTPError:
        return result
    except AttributeError:
        return result
