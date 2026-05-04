import asyncio
import json

from pathlib import Path

class AsyncCache:
    def __init__(self, limit: int = 20):
        self.cache = {}          # final results
        self.in_flight = {}      # key -> Future
        self.sem = asyncio.Semaphore(limit)
        self.lock = asyncio.Lock()

    def make_key(self, category: str, value: str) -> str:
        return f"{category}:{value}"

    async def get(self, category: str, value: str, fetch_fn):
        key = self.make_key(category, value)

        # 1) Cache hit
        if key in self.cache:
            return self.cache[key]

        async with self.lock:
            # 2) already running -> reuse future
            if key in self.in_flight:
                future = self.in_flight[key]
            else:
                # 3) create placeholder (lock state)
                loop = asyncio.get_running_loop()
                future = loop.create_future()
                self.in_flight[key] = future

                # start task
                asyncio.create_task(self._run(key, future, fetch_fn))

        return await future

    async def _run(self, key, future, fetch_fn):
        async with self.sem:
            try:
                result = await fetch_fn()
                self.cache[key] = result
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            finally:
                async with self.lock:
                    self.in_flight.pop(key, None)

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f)

    def load(self, path: str):
        p = Path(path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                self.cache = json.load(f)