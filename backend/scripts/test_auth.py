import asyncio
import sys
import os
import httpx

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.iths import ths_client

async def test_auth():
    print("--- Testing Auth ---")
    url = f"{ths_client.base_url}/get_access_token"
    headers = {
        "Content-Type": "application/json",
        "refresh_token": ths_client.refresh_token
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth())
