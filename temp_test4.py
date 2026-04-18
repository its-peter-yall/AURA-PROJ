import asyncio
import os

# Set required env vars for KeyManager
os.environ['AURA_MASTER_KEY'] = 'your-32-char-base64-key-here!'
os.environ['REDIS_URL'] = 'redis://127.0.0.1:6379'
os.environ['OPENROUTER_API_KEY'] = 'sk-or-v1-...'

import redis.asyncio as aioredis

async def test_with_key_manager():
    from model_router.router import ModelRouter, get_default_router
    from model_router.config import RouterConfig
    from model_router.key_manager import KeyManager

    # Create KeyManager
    redis_client = aioredis.from_url('redis://127.0.0.1:6379', decode_responses=True)
    km = KeyManager(redis_client)

    # Create router with key manager
    config = RouterConfig.from_env()
    print(f"OpenRouter api_key from env: '{config.openrouter.api_key[:10]}...' if set, else empty")
    print(f"Test mode: {config.test_mode}")

    router = ModelRouter(config, key_manager=km)

    print(f"\nProviders registered: {list(router._providers.keys())}")

    if 'openrouter' not in router._providers:
        print("OpenRouter not auto-registered (likely due to empty api_key)")
        # Check if lazy registration would work
        try:
            api_key = await km.get_key("openrouter")
            print(f"Key in KeyManager: {'yes' if api_key else 'no'}")
        except Exception as e:
            print(f"KeyManager error: {e}")

    await redis_client.aclose()

asyncio.run(test_with_key_manager())