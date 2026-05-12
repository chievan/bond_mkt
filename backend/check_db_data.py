from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from app.models.bond import BondHistory

DATABASE_URL = "sqlite:///./data/bond_mkt.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_db():
    db = SessionLocal()
    # 查找最新的 10 条历史记录
    records = db.query(BondHistory).order_by(BondHistory.date.desc()).limit(10).all()
    
    print(f"Latest 10 records in DB:")
    for r in records:
        print(f"Code: {r.code}, Date: {r.date}, Yield: {r.yield_val}")
    
    db.close()

if __name__ == "__main__":
    check_db()
