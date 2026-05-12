from app.main import SessionLocal
from app.models.bond import BondHistory
from sqlalchemy import func

db = SessionLocal()
target_codes = ['250011.IB', '250420.IB', '250215.IB', '230025.IB']

print(f"{'Code':<12} | {'Count':<6} | {'Start Date':<12} | {'End Date':<12} | {'Latest Yield'}")
print("-" * 65)

for code in target_codes:
    count = db.query(BondHistory).filter(BondHistory.code == code).count()
    earliest = db.query(BondHistory.date).filter(BondHistory.code == code).order_by(BondHistory.date.asc()).first()
    latest = db.query(BondHistory).filter(BondHistory.code == code).order_by(BondHistory.date.desc()).first()
    
    start_date = earliest[0] if earliest else "N/A"
    end_date = latest.date if latest else "N/A"
    yield_val = latest.yield_val if latest else "N/A"
    
    print(f"{code:<12} | {count:<6} | {str(start_date):<12} | {str(end_date):<12} | {yield_val}")

db.close()
