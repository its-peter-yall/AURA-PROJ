import asyncio
import httpx
import time

async def force_refresh_test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First call with refresh to force cache update
        print("Calling /models?refresh=true...")
        response = await client.get("http://127.0.0.1:8001/api/v1/settings/models?refresh=true")
        print(f"Status: {response.status_code}")
        data = response.json()

        api_models = [m for m in data if m['provider'] == 'openrouter']
        print(f"OpenRouter models after refresh: {len(api_models)}")

        # Check vendor distribution
        vendors = {}
        for m in api_models:
            v = m['name'].split('/')[0]
            vendors[v] = vendors.get(v, 0) + 1
        print(f"Vendors: {len(vendors)}")
        for v, c in sorted(vendors.items(), key=lambda x: -x[1]):
            print(f"  {v}: {c}")

asyncio.run(force_refresh_test())