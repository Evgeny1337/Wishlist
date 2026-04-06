from ninja import NinjaAPI
from pydantic import BaseModel
from wishlist_app.api import router as wishlist_router
api = NinjaAPI()


api.add_router('/wishlist/',wishlist_router)