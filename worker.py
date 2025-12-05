import asyncio
from core.task_queue import TaskQueue, TaskPriority

async def worker_main():
    print("Starting worker node...")
    queue = TaskQueue()
    try:
        await queue.initialize()
        print("Connected to Redis successfully.")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        # In production this should crash or retry, but for audit we exit
        return

    # In a real worker, we would register handlers here
    # queue.register_handler("some_task", some_handler)

    print("Workers initialized. Waiting for tasks...")
    await queue.start_workers(num_workers=3)

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Worker shutting down...")
        await queue.stop_workers()

if __name__ == "__main__":
    try:
        asyncio.run(worker_main())
    except KeyboardInterrupt:
        pass
