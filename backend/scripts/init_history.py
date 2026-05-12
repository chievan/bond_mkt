import asyncio
import sys
import os

# Add parent directory to path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.main import SessionLocal
from app.models.bond import BenchmarkConfig
from app.services.iths import sync_bond_history

DEFAULT_BENCHMARKS = {
  '国债': {
    '1Y': '230025.IB', '2Y': '240010.IB', '3Y': '250010.IB', '5Y': '250003.IB', 
    '7Y': '250007.IB', '10Y': '250011.IB', '20Y': '2500004.IB', '30Y': '2500002.IB', '50Y': '2500003.IB'
  },
  '国开债': {
    '1Y': '210208.IB', '2Y': '250202.IB', '3Y': '240203.IB', '5Y': '250208.IB', 
    '7Y': '220210.IB', '10Y': '250215.IB', '20Y': '09230220.IB'
  },
  '农发债': {
    '1Y': '250431.IB', '2Y': '220407.IB', '3Y': '250413.IB', '5Y': '250415.IB', 
    '7Y': '230402.IB', '10Y': '250420.IB'
  },
  '口行债': {
    '1Y': '250361.IB', '2Y': '170303.IB', '3Y': '250313.IB', '5Y': '200311.IB', 
    '7Y': '220311.IB', '10Y': '240311.IB'
  },
  '地方政府债': {
    '3Y': '198898.IB', '5Y': '2371176.IB', '7Y': '2205352.IB', '10Y': '2005291.IB', 
    '15Y': '232956.IB', '20Y': '234941.IB', '30Y': '2505080.IB'
  }
}

async def init_benchmarks_and_history():
    db = SessionLocal()
    try:
        all_codes = set()
        print("--- Initializing Benchmark Configs ---")
        for bond_type, tenors in DEFAULT_BENCHMARKS.items():
            for tenor, code in tenors.items():
                all_codes.add(code)
                # Save config if not exists
                existing = db.query(BenchmarkConfig).filter(
                    BenchmarkConfig.bond_type == bond_type,
                    BenchmarkConfig.tenor == tenor
                ).first()
                
                if not existing:
                    print(f"Adding default config: {bond_type} {tenor} -> {code}")
                    db.add(BenchmarkConfig(bond_type=bond_type, tenor=tenor, code=code))
                else:
                    existing.code = code # Force update to match current requested defaults
        
        db.commit()
        
        print("\n--- Batch Syncing Bond History (2020-Present) ---")
        print(f"Total unique codes to sync: {len(all_codes)}")
        
        # This will call the sync logic we just implemented
        await sync_bond_history(db, list(all_codes))
        
        print("\n--- Batch Sync Completed Successfully ---")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(init_benchmarks_and_history())
