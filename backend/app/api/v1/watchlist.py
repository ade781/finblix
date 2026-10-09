from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.asset import Asset, UserWatchlist

router = APIRouter()

@router.get("")
@router.get("/")
def get_user_watchlist(db: Session = Depends(get_db)):
    items = db.query(UserWatchlist).filter(UserWatchlist.user_name == "default_trader").all()
    results = []
    for item in items:
        asset = db.query(Asset).filter(Asset.id == item.asset_id).first()
        if asset:
            results.append({
                "id": item.id,
                "asset_id": asset.id,
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "base_currency": asset.base_currency,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })
    return {"status": "success", "count": len(results), "data": results}

@router.post("/{asset_id}")
def add_to_watchlist(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    existing = db.query(UserWatchlist).filter(
        UserWatchlist.user_name == "default_trader",
        UserWatchlist.asset_id == asset_id
    ).first()
    if existing:
        return {"status": "success", "message": "Already in watchlist"}

    new_item = UserWatchlist(user_name="default_trader", asset_id=asset_id)
    db.add(new_item)
    db.commit()
    return {"status": "success", "message": f"{asset.symbol} added to watchlist"}

@router.delete("/{asset_id}")
def remove_from_watchlist(asset_id: int, db: Session = Depends(get_db)):
    item = db.query(UserWatchlist).filter(
        UserWatchlist.user_name == "default_trader",
        UserWatchlist.asset_id == asset_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in watchlist")
        
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Removed from watchlist"}
