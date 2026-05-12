from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from .models.bond import Base, BondYield, BondSpread, BondQuantile, BenchmarkConfig, BondHistory
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from .services.iths import sync_all_curves, sync_bond_history
from .services.ai import ai_service
from pydantic import BaseModel

load_dotenv()

# SQLite Database Setup
DATABASE_URL = "sqlite:///./data/bond_mkt.db"
os.makedirs("./data", exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bond Market Tracker API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    message: str

class BenchmarkSaveRequest(BaseModel):
    bond_type: str
    benchmarks: Dict[str, str] # { "1Y": "230025.IB", ... }

@app.post("/sync")
async def sync_data(date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    success = await sync_all_curves(db, date)
    if success:
        return {"status": "success", "message": f"Data synchronized from iFinD for {date or 'today'}"}
    else:
        raise HTTPException(status_code=500, detail="Sync failed")

@app.get("/latest-date")
def get_latest_date(target: Optional[str] = Query(None), db: Session = Depends(get_db)):
    from .models.bond import BondHistory
    
    if target == "history":
        history_date = db.query(BondHistory.date).order_by(BondHistory.date.desc()).first()
        date_val = history_date[0] if history_date else None
    elif target == "curves":
        yield_date = db.query(BondYield.date).order_by(BondYield.date.desc()).first()
        date_val = yield_date[0] if yield_date else None
    else:
        # Default: Max of both
        yield_date = db.query(BondYield.date).order_by(BondYield.date.desc()).first()
        history_date = db.query(BondHistory.date).order_by(BondHistory.date.desc()).first()
        dates = []
        if yield_date: dates.append(yield_date[0])
        if history_date: dates.append(history_date[0])
        date_val = max(dates) if dates else None

    if not date_val:
        return {"date": datetime.now().strftime("%Y-%m-%d")}
        
    return {"date": date_val.strftime("%Y-%m-%d") if hasattr(date_val, 'strftime') else str(date_val)}

@app.get("/yields")
def get_yields(date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Returns yield curve data formatted for the frontend.
    If date is not provided, returns the latest available data.
    """
    if not date:
        # Get the latest date available in the DB
        latest = db.query(BondYield.date).order_by(BondYield.date.desc()).first()
        if not latest: return {"curves": {}}
        target_date = latest[0]
    else:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()

    records = db.query(BondYield).filter(BondYield.date == target_date).all()
    
    # Map DB records to Frontend structure
    curves = {}
    terms_map = {
        "y0": "0Y", "m1": "1M", "m2": "2M", "m3": "3M", "m6": "6M", "m9": "9M",
        "y1": "1Y", "y2": "2Y", "y3": "3Y", "y4": "4Y", "y5": "5Y", "y6": "6Y",
        "y7": "7Y", "y8": "8Y", "y9": "9Y", "y10": "10Y", "y15": "15Y",
        "y20": "20Y", "y30": "30Y", "y40": "40Y", "y50": "50Y"
    }

    # Find a global prev_date for display (use the first record's prev_date)
    display_prev_date = None
    
    for rec in records:
        # 1. Find the most recent date before target_date that has ANY data for this bond_type
        prev_date_rec = db.query(BondYield.date).filter(
            BondYield.date < target_date,
            BondYield.bond_type == rec.bond_type
        ).order_by(BondYield.date.desc()).first()
        
        prev_date = prev_date_rec[0] if prev_date_rec else None
        if not display_prev_date:
            display_prev_date = prev_date.strftime("%Y-%m-%d") if prev_date else None
        
        # 2. Fetch all values for that specific previous date
        prev_rec = None
        if prev_date:
            prev_rec = db.query(BondYield).filter(
                BondYield.date == prev_date,
                BondYield.bond_type == rec.bond_type
            ).first()
            
        # 3. Fetch last 250 trading days for this bond type to calculate percentiles
        history_250 = db.query(BondYield).filter(BondYield.bond_type == rec.bond_type)\
            .order_by(BondYield.date.desc()).limit(250).all()
        
        points = []
        for field, term in terms_map.items():
            val = getattr(rec, field)
            if val is not None:
                prev_val = getattr(prev_rec, field) if prev_rec else val
                change_bp = (val - prev_val) * 100
                
                # Dynamic Percentile Calculation
                hist_vals = [getattr(h, field) for h in history_250 if getattr(h, field) is not None]
                if hist_vals:
                    percentile = sum(1 for v in hist_vals if v < val) / len(hist_vals)
                else:
                    percentile = 0.5
                
                points.append({
                    "term": term,
                    "yield": val,
                    "prev_yield": prev_val,
                    "change": round(change_bp, 2),
                    "percentile": round(percentile, 4)
                })
        curves[rec.bond_type] = points

    return {
        "curves": curves, 
        "date": target_date.strftime("%Y-%m-%d"),
        "prev_date": display_prev_date
    }

@app.get("/history-yields")
def get_yield_history(
    bond_type: str, 
    term: str, 
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns historical yield data for a specific bond type and tenor.
    """
    t = term.lower()
    if t.endswith('y'):
        field = 'y' + t.replace('y', '')
    elif t.endswith('m'):
        field = 'm' + t.replace('m', '')
    else:
        field = 'y' + t
        
    query = db.query(BondYield.date, getattr(BondYield, field)).filter(BondYield.bond_type == bond_type)
    
    if start_date:
        query = query.filter(BondYield.date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(BondYield.date <= datetime.strptime(end_date, "%Y-%m-%d").date())
        
    records = query.order_by(BondYield.date.asc()).all()
    
    return [
        {"date": r.date.strftime("%Y-%m-%d"), "yield": r[1]} 
        for r in records if r[1] is not None
    ]

@app.get("/yields/multi-history")
def get_yield_multi_history(
    bond_type: str, 
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Returns the yield curve for the last N trading days.
    """
    # 1. Get the last N dates for this bond_type
    dates_records = db.query(BondYield.date).filter(
        BondYield.bond_type == bond_type
    ).order_by(BondYield.date.desc()).limit(limit).all()
    
    dates = [r[0] for r in dates_records]
    
    # 2. Map and fetch records
    results = []
    terms_map = {
        "y0": "0Y", "m1": "1M", "m2": "2M", "m3": "3M", "m6": "6M", "m9": "9M",
        "y1": "1Y", "y2": "2Y", "y3": "3Y", "y4": "4Y", "y5": "5Y", "y6": "6Y",
        "y7": "7Y", "y8": "8Y", "y9": "9Y", "y10": "10Y", "y15": "15Y",
        "y20": "20Y", "y30": "30Y", "y40": "40Y", "y50": "50Y"
    }
    
    for d in dates:
        rec = db.query(BondYield).filter(BondYield.date == d, BondYield.bond_type == bond_type).first()
        if rec:
            points = []
            for field, term in terms_map.items():
                val = getattr(rec, field)
                if val is not None:
                    points.append({"term": term, "yield": val})
            results.append({"date": d.strftime("%Y-%m-%d"), "points": points})
            
    return results

@app.post("/chat")
async def chat_with_ai(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        answer = await ai_service.analyze_market(db, req.message)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Benchmark Config & Bond History ---

@app.get("/benchmarks")
def get_benchmarks(bond_type: str, db: Session = Depends(get_db)):
    configs = db.query(BenchmarkConfig).filter(BenchmarkConfig.bond_type == bond_type).all()
    return {c.tenor: c.code for c in configs}

@app.post("/benchmarks/save")
async def save_benchmarks(req: BenchmarkSaveRequest, db: Session = Depends(get_db)):
    for tenor, code in req.benchmarks.items():
        db_config = db.query(BenchmarkConfig).filter(
            BenchmarkConfig.bond_type == req.bond_type,
            BenchmarkConfig.tenor == tenor
        ).first()
        
        if db_config:
            db_config.code = code
        else:
            db_config = BenchmarkConfig(bond_type=req.bond_type, tenor=tenor, code=code)
            db.add(db_config)
            
    db.commit()
    return {"status": "success"}

@app.post("/sync-bond-history")
async def sync_bond_history_endpoint(codes: List[str], db: Session = Depends(get_db)):
    success = await sync_bond_history(db, codes)
    if success:
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="History sync failed")

@app.get("/bond-history")
def get_bond_history(code: str, db: Session = Depends(get_db)):
    records = db.query(BondHistory).filter(BondHistory.code == code).order_by(BondHistory.date.asc()).all()
    return [
        {"date": r.date.strftime("%Y-%m-%d"), "yield": r.yield_val} 
        for r in records
    ]

@app.get("/")
def read_root():
    return {"message": "Bond Market Tracker API - Active"}

@app.get("/bond-valuations-batch")
def get_bond_valuations_batch(codes: str, date: str, db: Session = Depends(get_db)):
    try:
        query_date = datetime.strptime(date, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
    code_list = [c.strip() for c in codes.split(',') if c.strip()]
    records = db.query(BondHistory).filter(
        BondHistory.code.in_(code_list),
        BondHistory.date == query_date
    ).all()
    return {r.code: r.yield_val for r in records}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
