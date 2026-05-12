import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import sys

# Add parent dir to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.models.bond import Base, BondYield, BondSpread, BondQuantile

DATABASE_URL = "sqlite:///./data/bond_mkt.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def import_data(excel_path):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Read the Excel file
        # The user provided file name: 1-成交情况与利差基差V2.xlsx
        xls = pd.ExcelFile(excel_path)
        
        # We'll take the first sheet for historical data if it exists
        # In the previous check, sheet names were "2020年以来分位数", "2021年以来分位数"
        # Let's use the most recent one or combine them
        sheet_name = "2021年以来分位数"
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        
        for index, row in df.iterrows():
            date_val = row['指标名称']
            if not isinstance(date_val, (datetime, pd.Timestamp)):
                try:
                    date_val = pd.to_datetime(date_val).date()
                except:
                    continue
            else:
                date_val = date_val.date()

            # Map Yields
            # 中债国债到期收益率:1年, 2年, 3年, 5年, 7年, 10Y, 30Y
            yield_data = BondYield(
                date=date_val,
                y1=row.get('中债国债到期收益率:1年'),
                y2=row.get('中债国债到期收益率:2年'),
                y3=row.get('中债国债到期收益率:3年'),
                y5=row.get('中债国债到期收益率:5年'),
                y7=row.get('中债国债到期收益率:7年'),
                y10=row.get('中债国债到期收益率:10年'),
                y30=row.get('中债国债到期收益率:30年')
            )
            db.merge(yield_data)

            # Map Spreads
            spread_data = BondSpread(
                date=date_val,
                s10y_2y=row.get('10Y-2Y'),
                s5y_3y=row.get('5Y-3Y'),
                s7y_5y=row.get('7Y-5Y'),
                s10y_7y=row.get('10Y-7Y')
            )
            db.merge(spread_data)

        db.commit()
        print("Data imported successfully!")

    except Exception as e:
        print(f"Error importing data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    excel_file = "../1-成交情况与利差基差V2.xlsx"
    import_data(excel_file)
