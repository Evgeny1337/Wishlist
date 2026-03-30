from ninja import NinjaAPI
from pydantic import BaseModel

api = NinjaAPI()

class HealthResponse(BaseModel):
    status: str


@api.get('/health')
def health(request):
    response = HealthResponse(status='ok')
    return response