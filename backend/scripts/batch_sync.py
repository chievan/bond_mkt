import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.iths import sync_all_curves, ths_client
from app.main import SessionLocal
from app.models.bond import BondYield

async def batch_sync(start_date_str, end_date_str):
    print(f"--- Starting Batch Sync from {start_date_str} to {end_date_str} ---")
    
    # 1. Test Token
    token = await ths_client.get_access_token()
    if not token:
        print("CRITICAL: iFinD Token Validation Failed. Please check USER_REFRESH_TOKEN.")
        return
    print("SUCCESS: iFinD Token Valid.")

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    current_date = start_date
    db = SessionLocal()
    
    success_count = 0
    fail_count = 0
    
    try:
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            # Skip weekends (optional, but iFinD might not have data)
            if current_date.weekday() >= 5:
                print(f"[{date_str}] Skipping Weekend.")
                current_date += timedelta(days=1)
                continue
                
            print(f"[{date_str}] Syncing...", end="", flush=True)
            try:
                # Sync logic for this specific date
                success = await sync_all_curves(db, date_str)
                if success:
                    print(" OK")
                    success_count += 1
                else:
                    print(" FAILED (No Data or Error)")
                    fail_count += 1
            except Exception as e:
                print(f" ERROR: {str(e)}")
                fail_count += 1
            
            current_date += timedelta(days=1)
            # Sleep slightly to avoid rate limiting
            await asyncio.sleep(0.5)
            
        # 2. Validation
        total_records = db.query(BondYield).count()
        print(f"\n--- Sync Complete ---")
        print(f"Dates Processed: {success_count} Success, {fail_count} Failed")
        print(f"Total Database Records (Yield Points): {total_records}")
        
        if total_records > 0:
            latest = db.query(BondYield).order_by(BondYield.date.desc()).first()
            print(f"Latest Data Date in DB: {latest.date}")
            print(f"Example Data (10Y CGB): {latest.y10}% on {latest.date}")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(batch_sync("2026-04-01", "2026-05-08"))
