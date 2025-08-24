import os, sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "farmhub.settings")
import django
django.setup()

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from django.conf import settings
from datetime import date
from typing import Optional, List, Dict, Any
from reporting.database import (
    get_farm_summary,
    get_milk_production_report,
    get_recent_activities,
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload  

@router.get("/reports/farm-summary")
def farm_summary_report(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return get_farm_summary()

@router.get("/reports/milk-production")
def milk_production_report(
    farm_id: Optional[int] = None,
    farmer_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:

    return get_milk_production_report(farm_id, farmer_id, start_date, end_date)

@router.get("/reports/recent-activities")
def recent_activities_report(
    limit: int = 10,
    farm_id: Optional[int] = None,
    farmer_id: Optional[int] = None,
    cow_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    
    return get_recent_activities(limit, farm_id, farmer_id, cow_id, start_date, end_date)
