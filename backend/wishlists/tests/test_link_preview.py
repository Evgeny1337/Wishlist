import httpx

from wishlists.link_preview import fetch_link_preview


def test_fetch_link_preview_happy_path(httpx_mock):
    httpx_mock.add_response(
        url="https://shop.example/item",
        text="""
            <html><head>
            <meta property="og:title" content="Nice gift" />
            <meta property="og:image" content="https://img.shop.example/item.jpg" />
            </head></html>
        """,
    )

    preview = fetch_link_preview("https://shop.example/item")

    assert preview["preview_title"] == "Nice gift"
    assert preview["preview_image_url"] == "https://img.shop.example/item.jpg"


def test_fetch_link_preview_http_error_returns_empty(httpx_mock):
    httpx_mock.add_exception(httpx.ReadTimeout("slow upstream"))

    preview = fetch_link_preview("https://timeout.example/item")

    assert preview == {"preview_title": "", "preview_image_url": ""}


def test_fetch_link_preview_missing_og_tags_returns_empty(httpx_mock):
    httpx_mock.add_response(
        url="https://plain.example/item",
        text="<html><head><title>No OG</title></head><body>ok</body></html>",
    )

    preview = fetch_link_preview("https://plain.example/item")

    assert preview == {"preview_title": "", "preview_image_url": ""}
