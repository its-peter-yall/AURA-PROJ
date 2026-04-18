import asyncio
import os

os.environ['AURA_MASTER_KEY'] = 'test-master-key-for-testing!'
os.environ['REDIS_URL'] = 'redis://redis.example.com:6379'  # Cloud Redis

async def check():
    from model_router.router import get_default_router

    try:
        router = get_default_router()
        print(f"Router providers: {list(router._providers.keys())}")
    except Exception as e:
        print(f"Error getting router: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(check())