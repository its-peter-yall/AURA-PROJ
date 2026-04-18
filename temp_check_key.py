import asyncio
import httpx

async def check_key_restrictions():
    # Try to get credit balance - this might reveal key restrictions
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"Authorization": "Bearer sk-or-v1-..."}
        response = await client.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers=headers
        )
        print(f"Credit balance response status: {response.status_code}")
        data = response.json()
        print(f"Data: {data}")

asyncio.run(check_key_restrictions())