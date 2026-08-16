from http import HTTPStatus
from typing import List

from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router, Status, Path
from ninja.errors import HttpError
from pydantic import PositiveInt, TypeAdapter, HttpUrl

from invites.auth import TelegramJWTAuth
from wishlists.access import  can_view_wish
from wishlists.models import GiftPlan, GiftPlanItem, Wish
from wishlists.schemas import GiftPlanRequest, GiftPlanResponse, DetailSchema, ValidationErrorSchema, \
    GiftPlanUpdateRequest, GiftPlanDeleteResponse, GiftPlanItemRequest, GiftPlanItemResponse, \
    GiftPlanItemPatchDeletePath, GiftPlanItemDeleteResponse

gift_plan_router = Router(auth=TelegramJWTAuth())


_UNPROCESSABLE = DetailSchema | ValidationErrorSchema


@gift_plan_router.post("/plan/", response={
    HTTPStatus.CREATED: GiftPlanResponse,
    HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
})
def create_gift_plan(request: HttpRequest, payload: GiftPlanRequest):
    owner = request.auth
    return Status(HTTPStatus.CREATED, GiftPlan.objects.create(
        owner=owner,
        title=payload.title,
        occurs_at=payload.occurs_at,
    ))


@gift_plan_router.get("/plan/", response={
    HTTPStatus.OK: List[GiftPlanResponse],
})
def get_gift_plan_list(request: HttpRequest):
    owner = request.auth
    gift_plans = GiftPlan.objects.filter(owner=owner)
    if not gift_plans.exists():
        return Status(HTTPStatus.OK, [])
    return Status(HTTPStatus.OK, gift_plans)


@gift_plan_router.get("/plan/{int:plan_id}", response={
    HTTPStatus.OK: GiftPlanResponse,
    HTTPStatus.NOT_FOUND: DetailSchema,
    HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
})
def get_gift_plan(request: HttpRequest, plan_id: PositiveInt):
    owner = request.auth
    gift_plan = get_object_or_404(GiftPlan, id=plan_id, owner=owner)
    return Status(HTTPStatus.OK, gift_plan)


@gift_plan_router.patch("/plan/{int:plan_id}", response={
    HTTPStatus.OK: GiftPlanResponse,
    HTTPStatus.NOT_FOUND: DetailSchema,
    HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
})
def update_gift_plan(request: HttpRequest, plan_id:PositiveInt, payload: GiftPlanUpdateRequest):
    owner = request.auth
    gift_plan = get_object_or_404(GiftPlan, id=plan_id, owner=owner)
    updates = payload.model_dump(exclude_unset=True)
    for attr, value in updates.items():
        setattr(gift_plan, attr, value)
    gift_plan.save(update_fields=list(updates))
    return Status(HTTPStatus.OK, gift_plan)


@gift_plan_router.delete("/plan/{int:plan_id}", response={
    HTTPStatus.OK: GiftPlanDeleteResponse,
    HTTPStatus.NOT_FOUND: DetailSchema,
})
def delete_gift_plan(request: HttpRequest, plan_id: PositiveInt):
    owner = request.auth
    gift_plan = get_object_or_404(GiftPlan, id=plan_id, owner=owner)
    gift_plan.delete()
    return Status(HTTPStatus.OK, GiftPlanDeleteResponse(
        plan_id=plan_id,
    ))


@gift_plan_router.post("/plan/{int:plan_id}/item/", response={
    HTTPStatus.CREATED: GiftPlanItemResponse,
    HTTPStatus.NOT_FOUND: DetailSchema,
    HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
})
def create_gift_plan_item(request: HttpRequest, plan_id: PositiveInt, payload: GiftPlanItemRequest):
    owner = request.auth
    gift_plan = get_object_or_404(GiftPlan, id=plan_id, owner=owner)
    wishes = Wish.objects.filter(Q(pk=payload.wish) & can_view_wish(owner))
    if payload.wish and not wishes.exists():
        raise HttpError(HTTPStatus.NOT_FOUND, "У вас нет прав на данный wishlist")
    gift_plan_item = GiftPlanItem()
    for attr, value in payload.model_dump(exclude_unset=True).items():
        if attr == 'wish':
            wish = wishes.first()
            gift_plan_item.wish = wish
            setattr(gift_plan_item, 'title', wish.title)
            setattr(gift_plan_item, 'url', TypeAdapter(HttpUrl).validate_python(wish.url))
        else:
            setattr(gift_plan_item, attr, value)
    gift_plan_item.plan = gift_plan
    gift_plan_item.save()
    return Status(HTTPStatus.CREATED, gift_plan_item)


@gift_plan_router.patch("/plan/{int:plan_id}/item/{int:item_id}", response={
    HTTPStatus.OK: GiftPlanItemResponse,
    HTTPStatus.NOT_FOUND: DetailSchema,
    HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
})
def update_gift_plan_item(request: HttpRequest, path: Path[GiftPlanItemPatchDeletePath], payload: GiftPlanItemRequest):
    owner = request.auth
    get_object_or_404(GiftPlan, id=path.plan_id, owner=owner)
    wishes = Wish.objects.filter(Q(pk=payload.wish) & can_view_wish(owner))
    if payload.wish and not wishes.exists():
        raise HttpError(HTTPStatus.NOT_FOUND, "У вас нет прав на данный wishlist")
    plan_item = get_object_or_404(GiftPlanItem, id=path.item_id, plan_id=path.plan_id)
    updates = payload.model_dump(exclude_unset=True)
    updated_fields = []
    for attr, value in updates.items():
        if attr == 'wish':
            wish = wishes.first()
            plan_item.wish = wish
            setattr(plan_item, 'title', wish.title)
            setattr(plan_item, 'url', TypeAdapter(HttpUrl).validate_python(wish.url))
            updated_fields.extend(['title', 'url', 'wish'])
        else:
            setattr(plan_item, attr, value)
            updated_fields.append(attr)
    plan_item.save(update_fields=updated_fields)
    return Status(HTTPStatus.OK, plan_item)


@gift_plan_router.delete("/plan/{int:plan_id}/item/{int:item_id}", response={
    HTTPStatus.OK: GiftPlanItemDeleteResponse,
    HTTPStatus.NOT_FOUND: DetailSchema,
    HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
})
def delete_gift_plan_item(request: HttpRequest, path: Path[GiftPlanItemPatchDeletePath]):
    owner = request.auth
    get_object_or_404(GiftPlan, id=path.plan_id, owner=owner)
    gift_plan_item = get_object_or_404(GiftPlanItem, id=path.item_id, plan_id=path.plan_id)
    gift_plan_item.delete()
    return Status(HTTPStatus.OK, GiftPlanItemDeleteResponse(
        item_id=path.item_id,
    ))


@gift_plan_router.get("/plan/{int:plan_id}/item/", response={
    HTTPStatus.OK: List[GiftPlanItemResponse],
    HTTPStatus.NOT_FOUND: DetailSchema,
    HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
})
def get_gift_plan_item_list(request: HttpRequest, plan_id: PositiveInt):
    owner = request.auth
    gift_plan = get_object_or_404(GiftPlan.objects.prefetch_related('plan_items'), id=plan_id, owner=owner)
    if gift_plan.plan_items.count() == 0:
        return Status(HTTPStatus.OK, [])
    return Status(HTTPStatus.OK, gift_plan.plan_items)


@gift_plan_router.get("/plan/{int:plan_id}/item/{int:item_id}", response={
    HTTPStatus.OK: GiftPlanItemResponse,
    HTTPStatus.NOT_FOUND: DetailSchema,
    HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
})
def get_gift_plan_item_detail(request: HttpRequest, path: Path[GiftPlanItemPatchDeletePath]):
    owner = request.auth
    get_object_or_404(GiftPlan, id=path.plan_id, owner=owner)
    gift_plan_item = get_object_or_404(GiftPlanItem, id=path.item_id, plan_id=path.plan_id)
    return Status(HTTPStatus.OK, gift_plan_item)










