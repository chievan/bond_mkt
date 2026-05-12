import asyncio
import sys
import os
import httpx
import json

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.iths import ths_client

async def debug_basic_service():
    print("--- Debugging Basic Data Service ---")
    token = await ths_client.get_access_token()
    if not token:
        print("Token failed.")
        return
    
    # EDB codes often look like this in basic_data_service
    # Function name: THS_EDB
    url = "https://quantapi.51ifind.com/api/v1/basic_data_service"
    headers = {"Content-Type": "application/json", "access_token": token}
    
    # Standard format for EDB in basic_data_service
    payload = {
        "codes": "S0059749",
        "indicators": "ths_edb_data_edb", # This might be the indicator for EDB value
        "indipara": "2026-05-07,2026-05-07"
    }
    
    print(f"Requesting URL: {url}")
    print(f"Payload: {json.dumps(payload)}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response Body: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_basic_service())
