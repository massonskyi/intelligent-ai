import asyncio

async def metrics_persist_task(metrics_service, interval_sec=300):
    while True:
        await asyncio.sleep(interval_sec)
        await metrics_service.save_snapshot()