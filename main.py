from fastapi import FastAPI
from app.routes import router
from app.test_route import test_router

app = FastAPI()  

app.include_router(router)
app.include_router(test_router)