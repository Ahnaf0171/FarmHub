import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "farmhub.settings")

import django  
django.setup()

from django.db.models import Sum, Q  
from core.models import ( 
    User,
    Farm,
    Cow,
    Activity,
    MilkProduction,
)


def get_farm_summary() -> Dict[str, Any]:
   
    total_farms = Farm.objects.count()
    total_farmers = User.objects.filter(role="farmer").count()
    total_cows = Cow.objects.count()
    total_milk = MilkProduction.objects.aggregate(total=Sum("quantity"))["total"] or 0

    return {
        "farms": total_farms,
        "farmers": total_farmers,
        "cows": total_cows,
        "total_milk_liters": float(total_milk),
    }


def get_milk_production_report(
    farm_id: Optional[int] = None,
    farmer_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> Dict[str, Any]:
    
    qs = (
        MilkProduction.objects
        .select_related("cow", "recorded_by", "cow__farm")
        .all()
    )

    if farm_id:
        qs = qs.filter(cow__farm_id=farm_id)

    if farmer_id:
        qs = qs.filter(
            Q(recorded_by_id=farmer_id) | Q(cow__farmer_id=farmer_id)
        )

    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)

    total_liters = qs.aggregate(total=Sum("quantity"))["total"] or 0
    count = qs.count()

    items: List[Dict[str, Any]] = []
    for mp in qs: 
        cow = mp.cow
        farm = cow.farm if cow else None
        farmer = mp.recorded_by

        items.append({
            "id": mp.id,
            "date": mp.date.isoformat() if mp.date else None,
            "quantity": float(mp.quantity),
            "cow_id": cow.id if cow else None,
            "cow_tag_number": getattr(cow, "tag_number", None),
            "farm_id": farm.id if farm else None,
            "farm_name": getattr(farm, "name", None),
            "farmer_id": farmer.id if farmer else None,
            "farmer_username": getattr(farmer, "username", None),
        })

    return {
        "count": count,
        "total_liters": float(total_liters),
        "items": items,
    }


def get_recent_activities(
    limit: int = 10,
    farm_id: Optional[int] = None,
    farmer_id: Optional[int] = None,
    cow_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
   
    qs = (
        Activity.objects
        .select_related("cow", "recorded_by", "cow__farm")
        .order_by("-date", "-created_at")
    )

    if farm_id:
        qs = qs.filter(cow__farm_id=farm_id)

    if farmer_id:
        qs = qs.filter(
            Q(recorded_by_id=farmer_id) | Q(cow__farmer_id=farmer_id)
        )

    if cow_id:
        qs = qs.filter(cow_id=cow_id)

    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)

    qs = qs[: max(0, int(limit)) or 10]

    items: List[Dict[str, Any]] = []
    for a in qs:
        cow = a.cow
        farm = cow.farm if cow else None
        user = a.recorded_by

        items.append({
            "id": a.id,
            "date": a.date.isoformat() if a.date else None,
            "activity_type": a.activity_type,
            "description": a.description,
            "category": a.category,
            "cow_id": cow.id if cow else None,
            "cow_tag_number": getattr(cow, "tag_number", None),
            "farm_id": farm.id if farm else None,
            "farm_name": getattr(farm, "name", None),
            "recorded_by_id": user.id if user else None,
            "recorded_by_username": getattr(user, "username", None),
        })

    return items
