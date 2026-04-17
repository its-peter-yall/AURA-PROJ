import asyncio
import sys

sys.path.insert(0, "D:/Peter/AURA Twin Proj/AURA-PROJ/AURA-CHAT")
sys.path.insert(0, "D:/Peter/AURA Twin Proj/AURA-PROJ/shared/model_router/src")

from backend.utils.vertex_ai_client import generate_content_stream


async def test():
    try:
        async for chunk in generate_content_stream(
            model_name="google/gemma-4-31b-it:free",
            contents=["hello"],
            generation_config=None,
            provider="openrouter",
        ):
            print("chunk:", chunk)
            break
    except Exception as e:
        import traceback

        traceback.print_exc()
        print("ERROR:", type(e).__name__, str(e)[:200])


asyncio.run(test())
