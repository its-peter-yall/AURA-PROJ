import asyncio
import redis.asyncio as redis_asyncio
import json

async def test_cache():
    from model_router.cache import get_cached_models
    from model_router.router import ModelRouter, get_default_router
    from model_router.config import RouterConfig

    # Create router
    router = ModelRouter(RouterConfig.from_env())

    # Try to get OpenRouter models directly from router
    print("Testing router.list_models('openrouter')...")
    try:
        models = await router.list_models('openrouter')
        print(f"  Got {len(models)} models from router")
        vendors = {}
        for m in models:
            v = m.name.split('/')[0] if '/' in m.name else 'none'
            vendors[v] = vendors.get(v, 0) + 1
        print(f"  Vendors: {len(vendors)}")
        for vend, cnt in sorted(vendors.items(), key=lambda x: -x[1])[:10]:
            print(f"    {vend}: {cnt}")
    except Exception as e:
        print(f"  Error: {e}")

    # Now try via cache
    print("\nTesting via cache...")
    try:
        redis_client = redis_asyncio.from_url('redis://127.0.0.1:6379', decode_responses=True)
        models = await get_cached_models('openrouter', redis_client, router, force_refresh=True)
        print(f"  Got {len(models)} models from cache")
        vendors = {}
        for m in models:
            v = m.name.split('/')[0] if '/' in m.name else 'none'
            vendors[v] = vendors.get(v, 0) + 1
        print(f"  Vendors: {len(vendors)}")
        for vend, cnt in sorted(vendors.items(), key=lambda x: -x[1])[:10]:
            print(f"    {vend}: {cnt}")
        await redis_client.aclose()
    except Exception as e:
        print(f"  Error: {e}")

asyncio.run(test_cache())