import asyncio
import httpx

async def check():
    # First check with refresh=true
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Calling with refresh=true...")
        response = await client.get("http://127.0.0.1:8001/api/v1/settings/models?refresh=true")
        print(f"Status: {response.status_code}")
        data = response.json()

        by_provider = {}
        for m in data:
            p = m['provider']
            if p not in by_provider:
                by_provider[p] = []
            by_provider[p].append(m)

        print("Models after refresh:")
        for p, models in sorted(by_provider.items()):
            print(f'  {p}: {len(models)}')

        # Check OpenRouter count
        or_count = len([m for m in data if m['provider'] == 'openrouter'])
        print(f'\nTotal OpenRouter models after refresh: {or_count}')

asyncio.run(check())