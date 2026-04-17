
import os
import asyncio
from dotenv import load_dotenv
import sys
import httpx

async def main():
    # Load .env
    load_dotenv("AURA-CHAT/.env")
    
    # Try to reach the local server if it's running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8000/api/v1/settings/models")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                models = response.json()
                print(f"Models count: {len(models)}")
                for m in models:
                    print(f"- {m['name']} ({m['provider']}): type={m.get('model_type')}")
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Could not reach server: {e}")

if __name__ == "__main__":
    asyncio.run(main())
