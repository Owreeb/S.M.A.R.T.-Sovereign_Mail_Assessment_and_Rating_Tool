import asyncio
import json
import os
from pathlib import Path


class AsyncCache:
    def __init__(self, limit: int = 20):
        self.cache = {}  # {key: {method: result}}
        self.in_flight = {}  # (key, method) -> Future
        self.sem = asyncio.Semaphore(limit)
        self.lock = asyncio.Lock()

    def make_key(self, key: str, method: str) -> tuple:
        return (key, method)

    async def get(self, key: str, method: str, fetch_fn):
        cache_key = self.make_key(key, method)

        # 1) Cache hit - verschachtelte Struktur
        if key in self.cache:
            if method in self.cache[key]["errors"]:
                return

            if method in self.cache[key]:
                return self.cache[key][method]

        async with self.lock:
            # 2) already running -> reuse future
            if cache_key in self.in_flight:
                future = self.in_flight[cache_key]
            else:
                # 3) create placeholder (lock state)
                loop = asyncio.get_running_loop()
                future = loop.create_future()
                self.in_flight[cache_key] = future

                # start task
                asyncio.create_task(self._run(key, method, cache_key, future, fetch_fn))

        return await future

    async def _run(self, key, method, cache_key, future, fetch_fn):
        async with self.sem:
            try:
                if key not in self.cache:
                    self.cache[key] = {"errors": {}}

                result = await fetch_fn()
                self.cache[key][method] = result

                future.set_result(result)
            except Exception as e:
                self.cache[key]["errors"][method] = {
                    "type": type(e).__name__,
                    "message": str(e),
                }
                if not future.done():
                    future.set_result(None)
            finally:
                async with self.lock:
                    self.in_flight.pop(cache_key, None)

    async def monitor(self, interval: float = 2):
        print("STARTING MONITORING")
        await asyncio.sleep(interval)
        while self.in_flight:
            os.system("cls" if os.name == "nt" else "clear")

            for (key, method), future in self.in_flight.items():
                status = "✓ done" if future.done() else "… running"
                print(f"{status} | {method} | {key}")
            print(f"ACTIVE TASKS: {len(self.in_flight)}\n")
            await asyncio.sleep(interval)
        print("ENDED MONITORING")

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

    def load(self, path: str):
        p = Path(path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                self.cache = json.load(f)