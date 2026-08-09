from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from ..schemas.scan import IngredientRequest, BarcodeRequest, ScanResponse, IngredientResult, ScoreBreakdown
from ..services.ingredient_engine import IngredientEngine
from ..services.nova_classifier import NovaClassifier
from ..services.off_client import OpenFoodFactsClient
from ..core.deps import get_current_user_optional
from ..core.database import get_db
from ..models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(prefix="/scan", tags=["scan"])

engine = IngredientEngine()
nova_classifier = NovaClassifier()
off_client = OpenFoodFactsClient()

@router.post("/analyse", response_model=ScanResponse)
async def analyse_ingredients(
    request: IngredientRequest,
    current_user: dict | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    user_profile = {"allergies": [], "conditions": []}
    if current_user:
        result = await db.execute(select(User).where(User.id == current_user["uid"]))
        user = result.scalars().first()
        if user:
            user_profile = {
                "user_id": user.id,
                "allergies": user.allergies or [],
                "conditions": user.conditions or []
            }
    
    analyzed = engine.analyze_ingredients(request.ingredients, user_profile=user_profile)
    nova_class = nova_classifier.classify(request.ingredients)
    score_data = engine.calculate_hs_score(analyzed, nova_class, user_profile=user_profile)
    
    return ScanResponse(
        ingredients=analyzed,
        safety_score=score_data["final_score"],
        nova_class=nova_class,
        breakdown=ScoreBreakdown(**score_data["breakdown"])
    )

@router.post("/barcode", response_model=ScanResponse)
async def analyse_barcode(
    request: BarcodeRequest,
    current_user: dict | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    product = await off_client.get_product(request.barcode)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in database")
    
    raw_ingredients = product.get("ingredients_text", "").split(",")
    raw_ingredients = [i.strip() for i in raw_ingredients if i.strip()]
    
    user_profile = {"allergies": [], "conditions": []}
    if current_user:
        result = await db.execute(select(User).where(User.id == current_user["uid"]))
        user = result.scalars().first()
        if user:
            user_profile = {
                "user_id": user.id,
                "allergies": user.allergies or [],
                "conditions": user.conditions or []
            }
    
    analyzed = engine.analyze_ingredients(raw_ingredients, user_profile=user_profile)
    nova_class = int(product.get("nova_group", 4))
    score_data = engine.calculate_hs_score(analyzed, nova_class, user_profile=user_profile)
    
    return ScanResponse(
        product_name=product.get("product_name", "Unknown"),
        brand=product.get("brands", "Unknown"),
        ingredients=analyzed,
        safety_score=score_data["final_score"],
        nova_class=nova_class,
        breakdown=ScoreBreakdown(**score_data["breakdown"]),
        nutrients=product.get("nutriments", {})
    )
