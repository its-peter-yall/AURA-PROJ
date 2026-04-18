import httpx
import json

async def save_models():
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": "Bearer sk-or-v1-..."}
        )
        with open("temp_models.json", "w", encoding="utf-8") as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)
        print("Saved")

import asyncio
asyncio.run(save_models())