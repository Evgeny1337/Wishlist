import json

import pytest
from datetime import datetime

@pytest.mark.django_db
def test_get_wishes_returns_list(client):
    response = client.get('/api/wishlist/')
    assert response.status_code == 200

@pytest.mark.django_db
def test_post_wish_item_returns_new_wish_item(client):
    data = {"title": "New Wish Item",
            "description": "New Wish Item Description",
            "price": 100, "url": "https://example.com",
            "image_url": "https://example.com/image.png",
             }
    response = client.post('/api/wishlist/', data=json.dumps(data),content_type="application/json",)
    print("Ручное тестирование")
    print(response.status_code, response.json())
    assert response.status_code == 201
    assert response.json()['title'] == 'New Wish Item'

