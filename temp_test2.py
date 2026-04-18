import asyncio
import httpx

async def test_openrouter_providers():
    from model_router.config import OpenRouterConfig
    from model_router.providers.openrouter import OpenRouterProvider, OpenRouterEmbeddingProvider

    config = OpenRouterConfig(
        api_key='sk-or-v1-...',
        base_url='https://openrouter.ai/api/v1',
        site_name='AURA'
    )

    gen_provider = OpenRouterProvider(config)
    embed_provider = OpenRouterEmbeddingProvider(config)

    gen_models = await gen_provider.list_models()
    embed_models = await embed_provider.list_models()

    print(f'Generation models: {len(gen_models)}')
    print(f'Embedding models: {len(embed_models)}')

    gen_vendors = {}
    for m in gen_models:
        vendor = m.name.split('/')[0] if '/' in m.name else 'none'
        gen_vendors[vendor] = gen_vendors.get(vendor, 0) + 1
    print(f'Gen vendors: {len(gen_vendors)}')
    for v, c in sorted(gen_vendors.items(), key=lambda x: -x[1]):
        print(f'  {v}: {c}')

asyncio.run(test_openrouter_providers())