import asyncio
import httpx

async def test_openrouter_list():
    config = {'api_key': 'sk-or-v1-...', 'base_url': 'https://openrouter.ai/api/v1', 'site_name': 'AURA'}

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        headers = {'Authorization': f"Bearer {config['api_key']}", 'X-Title': config['site_name']}
        response = await http_client.get(f"{config['base_url']}/models", headers=headers)
        response.raise_for_status()

        payload = response.json().get('data', [])
        print(f'OpenRouter returned {len(payload)} models')

        vendors = {}
        for item in payload:
            name = item.get('id', '')
            if isinstance(name, str) and '/' in name:
                vendor = name.split('/')[0]
            else:
                vendor = 'no-slash'
            vendors[vendor] = vendors.get(vendor, 0) + 1

        print(f'Vendors: {len(vendors)}')
        for v, c in sorted(vendors.items(), key=lambda x: -x[1])[:10]:
            print(f'  {v}: {c}')

asyncio.run(test_openrouter_list())