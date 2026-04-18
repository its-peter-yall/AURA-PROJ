import asyncio
import httpx

async def test_api_models():
    # Get from API
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get("http://127.0.0.1:8001/api/v1/settings/models")
        api_models = [m for m in response.json() if m['provider'] == 'openrouter']

    # Get directly from OpenRouter
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"Authorization": "Bearer sk-or-v1-..."}
        response = await client.get("https://openrouter.ai/api/v1/models", headers=headers)
        or_models = response.json().get('data', [])

    # Compare
    api_names = set(m['name'] for m in api_models)
    or_names = set(m['id'] for m in or_models)

    in_api = api_names & or_names
    missing_from_api = or_names - api_names
    in_api_only = api_names - or_names

    print(f"API has {len(api_names)} OpenRouter models")
    print(f"OpenRouter has {len(or_names)} models")
    print(f"In both: {len(in_api)}")
    print(f"Missing from API (in OpenRouter but not API): {len(missing_from_api)}")
    print(f"In API but not in OpenRouter: {len(in_api_only)}")

    if missing_from_api:
        print(f"\nFirst 20 missing from API:")
        for name in sorted(missing_from_api)[:20]:
            print(f"  {name}")

asyncio.run(test_api_models())