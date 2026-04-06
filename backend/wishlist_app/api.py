from ninja import Router
from .schemas import WishlistItem
from .models import Wishlist
router = Router()

@router.get('', response=list[WishlistItem])
def get_wishes(request):
    return Wishlist.objects.all().order_by('-created_at')

@router.post('', response=WishlistItem)
def create_wish_item(wish_item: WishlistItem):
    new_wishlist = Wishlist.objects.create(
        name=wish_item.name,
        description=wish_item.description,
        price=wish_item.price,
        url=wish_item.url,
        image_url=wish_item.image_url,
    )
    return new_wishlist