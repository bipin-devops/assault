import asyncio
import time
import os
import requests


def fetch(url):
    """Make the request and return the result"""
    started_at = time.monotonic()
    response = requests.get(url)
    request_time = time.monotonic() - started_at
    return {"status_code": response.status_code, "request_time": request_time}


async def worker(name, queue, results):
    """A function to take unamke requests from a queue and perform the work and then add results to the result list"""
    loop = asyncio.get_event_loop()
    while True:
        url = await queue.get()
        if os.getenv("DEBUG"):
            print(f"{name} - Fetching {url}")
        future_results = loop.run_in_executor(None, fetch, url)
        result = await future_results
        results.append(result)
        queue.task_done()


async def distribute_work(url, requests, concurrency, results):
    """Divide up the work into batches and collect the final result"""
    queue = asyncio.Queue()
    for _ in range(requests):
        queue.put_nowait(url)

    tasks = []
    for i in range(concurrency):
        task = asyncio.create_task(worker(f"worker- {i+1}", queue, results))
        tasks.append(task)

    started_at = time.monotonic()
    await queue.join()
    total_time = time.monotonic() - started_at

    for task in tasks:
        task.cancel()

    print("-------")
    print(
        f"{concurrency} workers took {total_time:.2f} seconds to compplete {len(results)} requests"
    )


def assault(url, requests, concurrency):
    """Entry point to making requests"""
    results = []
    asyncio.run(distribute_work(url, requests, concurrency, results))
    print(results)
