from ninja import NinjaAPI
from pydantic import BaseModel
from invites.api import router as InviteRouter

api = NinjaAPI()

api.add_router('/invites/', InviteRouter)

class HealthResponse(BaseModel):
    status: str


@api.get('/health')
def health(request):
    response = HealthResponse(status='ok')
    return response