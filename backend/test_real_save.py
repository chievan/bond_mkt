import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.bond import BondHistory
from app.services.iths import ITHSClient, sync_bond_history

load_dotenv()

DATABASE_URL = "sqlite:///./data/bond_mkt.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

async def test_save_to_db():
    db = SessionLocal()
    token = os.getenv("ITHS_REFRESH_TOKEN")
    client = ITHSClient(token)
    
    # 我们只测 250011.IB
    code = "250011.IB"
    print(f"Starting real sync for {code}...")
    
    # 直接调用业务逻辑函数
    success = await sync_bond_history(db, [code])
    
    if success:
        print("Sync function returned success.")
        # 再次检查数据库
        record = db.query(BondHistory).filter(BondHistory.code == code, BondHistory.date == '2026-05-11').first()
        if record:
            print(f"SUCCESS: Found 5.11 record in DB: {record.yield_val}")
        else:
            print("FAILED: 5.11 record still missing in DB after sync.")
    else:
        print("Sync function returned failure.")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_save_to_db())
