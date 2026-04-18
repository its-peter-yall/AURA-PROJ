import asyncio
import httpx

async def save():
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get("http://127.0.0.1:8001/api/v1/settings/models")
        data = response.json()
        with open('temp_api_models.txt', 'w') as f:
            for m in data:
                if m['provider'] == 'openrouter':
                    f.write(m['name'] + '\n')
        print(f"Saved {len([m for m in data if m['provider'] == 'openrouter'])} models")

asyncio.run(save())