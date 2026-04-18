import asyncio
import os

os.environ['AURA_MASTER_KEY'] = 'test-master-key-for-testing!'
os.environ['REDIS_URL'] = 'redis://127.0.0.1:6379'

import redis.asyncio as aioredis

async def check_cache_status():
    from model_router.cache import get_cached_models
    from model_router.router import ModelRouter
    from model_router.config import RouterConfig

    # Create router WITHOUT key manager first
    config = RouterConfig.from_env()
    print(f"Config test_mode: {config.test_mode}")
    print(f"Config openrouter api_key: '{config.openrouter.api_key[:10]}...' " if config.openrouter.api_key else "Config openrouter api_key: EMPTY")

    router = ModelRouter(config, key_manager=None)
    print(f"Providers: {list(router._providers.keys())}")

    # Try listing with refresh
    if 'openrouter' in router._providers:
        try:
            models = await router.list_models('openrouter')
            print(f"Router list_models returned {len(models)} models")
        except Exception as e:
            print(f"Router list_models error: {e}")
    else:
        print("OpenRouter not in providers, trying lazy registration...")

        # Check if lazy registration would work with a mock key manager
        redis_client = aioredis.from_url('redis://127.0.0.1:6379', decode_responses=True)
        try:
            from model_router.key_manager import KeyManager
            km = KeyManager(redis_client)
            # Store a test key
            try:
                await km.store_key('openrouter', 'sk-or-v1-test-key-for-testing')
                print("Stored test key in KeyManager")
            except Exception as e:
                print(f"Could not store key: {e}")

            # Try again with key manager
            router2 = ModelRouter(config, key_manager=km)
            print(f"Providers after with key manager: {list(router2._providers.keys())}")

            if 'openrouter' in router2._providers:
                models = await router2.list_models('openrouter')
                print(f"Router2 list_models returned {len(models)} models")
        except Exception as e:
            print(f"KeyManager error: {e}")
        finally:
            await redis_client.aclose()

asyncio.run(check_cache_status())