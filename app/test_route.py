from fastapi import APIRouter

test_router = APIRouter()

@test_router.get("/test")
def test_api():
    return {"message": "健康"}