from ninja import Schema, ModelSchema
from pydantic import Field, PositiveInt, HttpUrl

from wishlists.models import WishList, Wish


class ErrorSchema(Schema):
    detail: dict[str,str] = Field(description='Ошибка валидации')


class WishListDeletedResponse(Schema):
    deleted_count: PositiveInt = Field(description='Количиство удаленных')
    details: dict[str, int] = Field(description='Количество удаленных объектов')


class WishListCreateRequest(Schema):
    init_data: str = Field(description='Авторизационные данные')
    title: str = Field(description='Заголовок', min_length=1)

class WishListDeleteGet(Schema):
    init_data: str = Field(description='Авторизационные данные', min_length=1)
    wishlist_id: PositiveInt = Field(description="ID Вишлиста")


class WishListResponseSchema(ModelSchema):
    class Meta:
        model = WishList
        fields = ['id', 'owner', 'title', 'created_at']


class WishCreateRequest(Schema):
    init_data: str = Field(description='Авторизационные данные', min_length=1)
    title: str = Field(description='Заголовок', min_length=1)
    url: HttpUrl | None = Field(description='Ссылка', default=None)
    note: str = Field(description='Описание', default='')

class WishCreateResponse(ModelSchema):
    wishlist_id:int = Field(description='ID Вишлиста')

    class Meta:
        model = Wish
        fields = ['id', 'title', 'url', 'note', 'created_at']



