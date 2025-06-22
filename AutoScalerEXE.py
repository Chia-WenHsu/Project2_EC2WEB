import asyncio
from app.AutoScaler import scale_app_instances
import os
import traceback

async def start_autoscaler_loop():
    print(f" AutoScaler running (PID={os.getpid()})")
    while True:
        try:
            await scale_app_instances()
        except Exception as e:
            print(f"[AutoScaler Error] {e}")
            traceback.print_exc()
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(start_autoscaler_loop())