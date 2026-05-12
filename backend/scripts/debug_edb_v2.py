import asyncio
import sys
import os
import httpx
import json

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.iths import ths_client

async def debug_edb_new_url():
    print("--- Debugging EDB Query (New URL) ---")
    token = await ths_client.get_access_token()
    if not token:
        print("Token failed.")
        return
    
    indicator = "S0059749"
    test_date = "2026-05-07"
    
    # Try the /ths_edb endpoint
    url = f"https://quantapi.51ifind.com/api/v1/ths_edb"
    headers = {"Content-Type": "application/json", "access_token": token}
    payload = {
        "indicators": indicator,
        "startdate": test_date,
        "enddate": test_date
    }
    
    print(f"Requesting URL: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response Body: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_edb_new_url())
