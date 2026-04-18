import asyncio
import httpx

async def check():
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://127.0.0.1:8001/api/v1/settings/models")
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f'Total models from API: {len(data)}')

            by_provider = {}
            for m in data:
                p = m['provider']
                if p not in by_provider:
                    by_provider[p] = []
                by_provider[p].append(m)

            for p, models in sorted(by_provider.items()):
                print(f'{p}: {len(models)} models')
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(check())