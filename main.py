from fastapi import FastAPI
from app.routes import router
from app.test_route import test_router
from app.AutoScaler import scale_app_instances
from app.AutoScaler import get_sqs_q_depth
from app.AutoScaler import get_current_app_instance
from aws_helper import start_background_response_poller

app = FastAPI()  

app.include_router(router)
app.include_router(test_router)


@app.get("/status")
async def status():
    depth = await get_sqs_q_depth()
    current_instances = await get_current_app_instance()
    current = len(current_instances)
    return {
        "queue_depth": depth,
        "current_instances": current
    }


@app.on_event("startup")
def startup_event():
    start_background_response_poller()