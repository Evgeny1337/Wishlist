from ninja import NinjaAPI
from pydantic import BaseModel
import invites.api
import invites.telegram_webapp


api = NinjaAPI()

api.add_router('/invites/', invites.api.router)
api.add_router('/telegram_webapp/', invites.telegram_webapp.router)

class HealthResponse(BaseModel):
    status: str


@api.get('/health')
def health(request):
    response = HealthResponse(status='ok')
    return response