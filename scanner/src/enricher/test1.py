import asyncio
from typing import Dict, Any, Callable, TypeVar, Awaitable

T = TypeVar('T')

class Singleflight:
    def __init__(self):
        self.in_flight: Dict[str, asyncio.Future] = {}
        self.lock = asyncio.Lock()

    async def do(self, key: str, fn: Callable[[], Awaitable[T]]) -> T:
        async with self.lock:
            if key in self.in_flight:
                # Request already in flight, wait for it
                return await self.in_flight[key]
            
            # Create a new future for this key
            future = asyncio.get_event_loop().create_future()
            self.in_flight[key] = future
            
            # Start the actual work in the background
            asyncio.create_task(self._execute(key, fn, future))

        # Wait for the result
        return await future

    async def _execute(self, key: str, fn: Callable, future: asyncio.Future):
        try:
            result = await fn()
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            # Clean up the in-flight record
            async with self.lock:
                self.in_flight.pop(key, None)

# Usage Example
async def expensive_db_query():
    await asyncio.sleep(1)  # Simulate slow DB call
    return "Data fetched"

async def main():
    sf = Singleflight()
    
    # Launch 10 concurrent requests with the same key
    tasks = [sf.do("user:123", expensive_db_query) for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    print(f"Received {len(results)} results from a single execution.")

asyncio.run(main())   