import httpx
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.bond import BondYield, BondSpread, BondHistory

class ITHSClient:
    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token
        self.access_token = None
        self.token_expiry = None
        self.base_url = "https://quantapi.51ifind.com/api/v1"

    async def get_access_token(self):
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        url = f"{self.base_url}/get_access_token"
        headers = {
            "Content-Type": "application/json",
            "refresh_token": self.refresh_token
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers)
                data = response.json()
                if data.get("errorcode") == 0:
                    self.access_token = data["data"]["access_token"]
                    self.token_expiry = datetime.now() + timedelta(days=6)
                    return self.access_token
                return None
            except Exception:
                return None

    async def fetch_edb_data(self, indicators: List[str], start_date: str, end_date: str):
        token = await self.get_access_token()
        if not token: return None

        # Correct URL from Super Command
        url = f"https://quantapi.51ifind.com/api/v1/edb_service"
        headers = {"Content-Type": "application/json", "access_token": token}
        payload = {
            "indicators": ",".join(indicators),
            "startdate": start_date if start_date else "",
            "enddate": end_date if end_date else ""
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                return response.json()
            except Exception:
                return None

    async def fetch_history_data(self, codes: List[str], start_date: str, end_date: str):
        token = await self.get_access_token()
        if not token: return None

        url = f"{self.base_url}/history_data"
        headers = {"Content-Type": "application/json", "access_token": token}
        payload = {
            "reqBody": {
                "codes": ",".join(codes),
                "indicators": "evaluate_yield_cb",
                "startdate": start_date,
                "enddate": end_date
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                return response.json()
            except Exception:
                return None

# --- Real Indicator Mapping from Super Command ---
BOND_INDICATORS = {
    "国债": {
        "0Y": "L003783671", "1M": "L003783672", "2M": "L003783673", "3M": "L001617903",
        "6M": "L001619651", "9M": "L001617904", "1Y": "L001618296", "2Y": "L001619275",
        "3Y": "L001618297", "4Y": "L001619899", "5Y": "L001619023", "6Y": "L001617905",
        "7Y": "L001619820", "8Y": "L001620136", "9Y": "L003783674", "10Y": "L001619604",
        "15Y": "L001618298", "20Y": "L001617906", "30Y": "L001618299", "40Y": "L004347685",
        "50Y": "L001617907"
    },
    "国开债": {
        "0Y": "L003783685", "1M": "L003783686", "2M": "L003783687", "3M": "L002959786",
        "6M": "L002959787", "9M": "L002959788", "1Y": "L002959789", "2Y": "L002959790",
        "3Y": "L002959791", "4Y": "L002959792", "5Y": "L002959793", "6Y": "L002959794",
        "7Y": "L002959795", "8Y": "L002959796", "9Y": "L003783688", "10Y": "L002959797",
        "15Y": "L002959798", "20Y": "L002959799", "30Y": "L002959800", "50Y": "L002959801"
    },
    "农发债": {
        "0Y": "L004226351", "1M": "L004226352", "2M": "L004226353", "3M": "L004226354",
        "6M": "L004226355", "9M": "L004226356", "1Y": "L004226357", "2Y": "L004226358",
        "3Y": "L004226359", "4Y": "L004226360", "5Y": "L004226361", "6Y": "L004226362",
        "7Y": "L004226363", "8Y": "L004226364", "9Y": "L004226365", "10Y": "L004226366",
        "15Y": "L004226367", "20Y": "L004226368", "30Y": "L011191473"
    },
    "口行债": {
        "0Y": "L004226333", "1M": "L004226334", "2M": "L004226335", "3M": "L004226336",
        "6M": "L004226337", "9M": "L004226338", "1Y": "L004226339", "2Y": "L004226340",
        "3Y": "L004226341", "4Y": "L004226342", "5Y": "L004226343", "6Y": "L004226344",
        "7Y": "L004226345", "8Y": "L004226346", "9Y": "L004226347", "10Y": "L004226348",
        "15Y": "L004226349", "20Y": "L004226350"
    },
    "地方政府债": {
        "1Y": "L011198462", "2Y": "L011198463", "3Y": "L011198464", "5Y": "L011198465",
        "7Y": "L011198466", "10Y": "L011198467", "15Y": "L011198468", "20Y": "L011198469",
        "30Y": "L011198470"
    }
}

USER_REFRESH_TOKEN = os.getenv("ITHS_REFRESH_TOKEN", "your_fallback_token_here")
ths_client = ITHSClient(USER_REFRESH_TOKEN)

async def sync_all_curves(db: Session, date_str: str = None):
    """
    Syncs all 5 bond categories for the specified date (default today).
    """
    target_date = date_str if date_str else datetime.now().strftime("%Y-%m-%d")
    
    for bond_type, mapping in BOND_INDICATORS.items():
        codes = list(mapping.values())
        raw_data = await ths_client.fetch_edb_data(codes, target_date, target_date)
        print(f"DEBUG raw_data: {raw_data}")
        
        if not raw_data or raw_data.get("errorcode") != 0:
            print(f"Error for {bond_type}: {raw_data}")
            continue
            
        print(f"Got data for {bond_type}: {len(raw_data.get('data', []))} items")
        # Parse THS response
        results = raw_data.get("tables", [])
        
        has_values = any(len(item.get("value", [])) > 0 for item in results)
        if not has_values:
            print(f"[{bond_type}] No data available for {target_date}.")
            continue
            
        # Build yield entry
        yield_data = {"date": datetime.strptime(target_date, "%Y-%m-%d").date(), "bond_type": bond_type}
        
        for item in results:
            id_list = item.get("id", [])
            if not id_list: continue
            
            indicator_id = id_list[0]
            tenor = next((k for k, v in mapping.items() if v == indicator_id), None)
            if tenor:
                if "M" in tenor:
                    field = "m" + tenor.replace("M", "")
                else:
                    field = "y" + tenor.replace("Y", "")
                    
                val_list = item.get("value", [])
                if val_list:
                    yield_data[field] = float(val_list[0])
        
        if len(yield_data) > 2: # Has at least one yield point
            # Delete existing for this date/type to avoid UC violation if merge is tricky
            db.query(BondYield).filter(
                BondYield.date == yield_data["date"],
                BondYield.bond_type == yield_data["bond_type"]
            ).delete()
            
            db_entry = BondYield(**yield_data)
            db.add(db_entry)
    
    db.commit()
    return True

async def sync_bond_history(db: Session, codes: List[str]):
    """
    Syncs historical valuation data for a list of bond codes.
    If no data in DB, starts from 2020-01-01.
    If data exists, starts from max(date) + 1 day.
    """
    if not codes: return True
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    for code in codes:
        # Determine start date
        latest = db.query(BondHistory.date).filter(BondHistory.code == code).order_by(BondHistory.date.desc()).first()
        if latest:
            # latest[0] is a Date object (not string) based on model
            start_date = (latest[0] + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            start_date = "2020-01-01"
            
        if start_date > today: continue
        
        raw_data = await ths_client.fetch_history_data([code], start_date, today)
        
        if not raw_data or raw_data.get("errorcode") != 0:
            print(f"Error fetching history for {code}: {raw_data}")
            continue
            
        # Parse history data based on 'tables' format
        tables = raw_data.get("tables", [])
        if not tables: continue
        
        for table_item in tables:
            actual_code = table_item.get("thscode")
            times = table_item.get("time", [])
            yields = table_item.get("table", {}).get("evaluate_yield_cb", [])
            
            for i in range(len(times)):
                if i >= len(yields) or yields[i] is None: continue
                
                try:
                    date_val = datetime.strptime(times[i], "%Y-%m-%d").date()
                    db_entry = BondHistory(code=actual_code, date=date_val, yield_val=float(yields[i]))
                    db.merge(db_entry)
                except Exception as e:
                    print(f"Error saving history row: {e}")
        
        db.commit()
    
    return True
