from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.history import ScanHistory
from ..schemas.user import UserProfileResponse, UserProfileUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve the current user's profile.
    
    If the user does not have a profile yet, one will be automatically created with empty defaults.
    Requires a valid Firebase authentication token.
    """
    uid = current_user["uid"]
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalars().first()
    
    if not user:
        # Auto-create row with empty defaults on first access
        user = User(
            id=uid,
            display_name=current_user.get("email"),
            allergies=[],
            conditions=[],
            goals=[]
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    return user

@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    request: UserProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current user's profile.
    
    Allows partial updates of allergies, conditions, goals, and display name.
    Requires a valid Firebase authentication token.
    """
    uid = current_user["uid"]
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
        
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
        
    await db.commit()
    await db.refresh(user)
    
    return user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete the current user's profile.
    
    This will permanently delete the user's profile and cascade delete all their scan history.
    Requires a valid Firebase authentication token.
    """
    uid = current_user["uid"]
    
    # Delete scan history first to cascade
    await db.execute(delete(ScanHistory).where(ScanHistory.user_id == uid))
    
    # Delete user profile
    result = await db.execute(delete(User).where(User.id == uid))
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User profile not found")
        
    await db.commit()
