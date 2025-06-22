from fastapi import FastAPI
from app.routes import router
from app.test_route import test_router
from app.AutoScaler import scale_app_instances
from app.AutoScaler import get_sqs_q_depth
from app.AutoScaler import get_current_app_instance
import asyncio

app = FastAPI()  

app.include_router(router)
app.include_router(test_router)

@app.on_event("startup")
async def startup_event():
    await asyncio.sleep(5) 
    print("System ready. Web API starting...")

    asyncio.create_task(start_autoscaler_loop())

async def start_autoscaler_loop():
    while True:
        try:
            scale_app_instances()
        except Exception as e:
            print(f"[AutoScaler Error] {e}")
        await asyncio.sleep(5)  


@app.get("/status")
def status():
    depth = get_sqs_q_depth()
    current = len(get_current_app_instance())
    return {
        "queue_depth": depth,
        "current_instances": current
    }