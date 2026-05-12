import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.iths import ths_client, BOND_INDICATORS

async def debug_iths():
    print("--- Debugging iFinD Connection ---")
    token = await ths_client.get_access_token()
    if not token:
        print("Token failed.")
        return
    
    # Try one indicator: 10Y CGB (S0059749)
    test_date = "2026-05-07"
    indicator = "S0059749"
    
    print(f"Fetching {indicator} for {test_date}...")
    res = await ths_client.fetch_edb_data([indicator], test_date, test_date)
    
    import json
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(debug_iths())
