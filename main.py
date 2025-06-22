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
async def start_autoscaler():
    async def scaler_loop():
        while True:
            try:
                scale_app_instances()
            except Exception as e:
                print(f"[AutoScaler Error] {e}")
            await asyncio.sleep(5)   

    asyncio.create_task(scaler_loop())  


@app.get("/status")
def status():
    depth = get_sqs_q_depth()
    current = len(get_current_app_instance())
    return {
        "queue_depth": depth,
        "current_instances": current
    }