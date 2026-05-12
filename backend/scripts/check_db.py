import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import SessionLocal
from app.models.bond import BondYield, Base

def check_db():
    db = SessionLocal()
    try:
        count = db.query(BondYield).count()
        print(f"Total BondYield records: {count}")
        
        if count > 0:
            all_rec = db.query(BondYield).all()
            for r in all_rec:
                print(f"Date: {r.date}, Type: {r.bond_type}, 10Y: {r.y10}")
        else:
            # Check if table exists
            from sqlalchemy import inspect
            inspector = inspect(db.bind)
            tables = inspector.get_table_names()
            print(f"Tables in DB: {tables}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
