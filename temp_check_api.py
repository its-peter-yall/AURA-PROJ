import asyncio
import httpx

async def check():
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "http://127.0.0.1:8001/api/v1/settings/models",
            headers={}
        )
        data = response.json()
        or_models = [m for m in data if m['provider'] == 'openrouter']
        print(f'OpenRouter models from API: {len(or_models)}')

        # Show all model names
        for m in or_models:
            print(f'  {m["name"]}')

asyncio.run(check())