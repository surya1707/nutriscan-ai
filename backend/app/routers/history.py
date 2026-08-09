from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from typing import List

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.history import ScanHistory
from ..schemas.history import ScanHistoryResponse

router = APIRouter(prefix="/history", tags=["history"])

async def get_scan_or_404(
    scan_id: int, 
    user_id: str, 
    db: AsyncSession
) -> ScanHistory:
    result = await db.execute(
        select(ScanHistory).where(
            ScanHistory.id == scan_id, 
            ScanHistory.user_id == user_id
        )
    )
    scan = result.scalars().first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Scan history not found or not owned by user"
        )
    return scan

@router.get("", response_model=List[ScanHistoryResponse])
async def list_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List the current user's scan history.
    
    Results are paginated and ordered by newest first.
    Requires a valid Firebase authentication token.
    """
    result = await db.execute(
        select(ScanHistory)
        .where(ScanHistory.user_id == current_user["uid"])
        .order_by(desc(ScanHistory.scanned_at))
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()

@router.get("/{id}", response_model=ScanHistoryResponse)
async def get_history_item(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a single scan history item by its ID.
    
    Returns 404 if the item does not exist or belongs to another user.
    Requires a valid Firebase authentication token.
    """
    return await get_scan_or_404(id, current_user["uid"], db)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history_item(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific scan history item.
    
    Returns 404 if the item does not exist or belongs to another user.
    Requires a valid Firebase authentication token.
    """
    scan = await get_scan_or_404(id, current_user["uid"], db)
    await db.delete(scan)
    await db.commit()

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear all scan history for the current user.
    
    Permanently deletes all history items owned by this user.
    Requires a valid Firebase authentication token.
    """
    await db.execute(
        delete(ScanHistory)
        .where(ScanHistory.user_id == current_user["uid"])
    )
    await db.commit()
