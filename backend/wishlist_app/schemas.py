from datetime import datetime
from pydantic import BaseModel, HttpUrl, ConfigDict, Field

class WishlistItem(BaseModel):
    title:str
    url:HttpUrl
    price:float | None
    image_url:HttpUrl | None
    description:str | None
    created_at:datetime | None
    model_config = ConfigDict(from_attributes=True)
