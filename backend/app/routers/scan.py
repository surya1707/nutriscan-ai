from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
from ..core.rate_limit import limiter
from ..schemas.scan import IngredientRequest, BarcodeRequest, ScanResponse, IngredientResult, ScoreBreakdown
from ..services.ingredient_engine import IngredientEngine
from ..services.nova_classifier import NovaClassifier
from ..services.off_client import OpenFoodFactsClient
from ..core.deps import get_current_user_optional
from ..core.database import get_db
from ..models.user import User
from ..models.history import ScanHistory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(prefix="/scan", tags=["scan"])

engine = IngredientEngine()
nova_classifier = NovaClassifier()
off_client = OpenFoodFactsClient()

@router.post("/analyse", response_model=ScanResponse)
@limiter.limit("30/minute")
async def analyse_ingredients(
    request: Request,
    body: IngredientRequest,
    current_user: dict | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a custom list of ingredients.
    
    This endpoint processes a raw list of ingredient strings, matches them against E-codes
    and known harmful keywords, and calculates a personalized health score if the user is authenticated.
    Authenticated scans are automatically saved to history.
    """
    user_profile = {"allergies": [], "conditions": [], "goals": []}
    if current_user:
        result = await db.execute(select(User).where(User.id == current_user["uid"]))
        user = result.scalars().first()
        if user:
            user_profile = {
                "user_id": user.id,
                "allergies": user.allergies or [],
                "conditions": user.conditions or [],
                "goals": user.goals or []
            }
    
    analyzed = engine.analyze_ingredients(body.ingredients, user_profile=user_profile)
    nova_class = nova_classifier.classify(body.ingredients)
    score_data = engine.calculate_hs_score(analyzed, nova_class, user_profile=user_profile)
    
    if current_user:
        history_entry = ScanHistory(
            user_id=current_user["uid"],
            product_name="Custom Scan",
            brand="Unknown",
            health_score=score_data["final_score"],
            nova_group=nova_class,
            nutrients={},
            ingredients=[i.model_dump() for i in analyzed] if analyzed else []
        )
        db.add(history_entry)
        await db.commit()
    
    return ScanResponse(
        ingredients=analyzed,
        safety_score=score_data["final_score"],
        nova_class=nova_class,
        breakdown=ScoreBreakdown(**score_data["breakdown"])
    )

@router.post("/barcode", response_model=ScanResponse)
@limiter.limit("30/minute")
async def analyse_barcode(
    request: Request,
    body: BarcodeRequest,
    current_user: dict | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a product via its barcode.
    
    This endpoint looks up the barcode in the Open Food Facts database. If found, it extracts
    the ingredients, classifies them, and calculates a personalized health score if the user
    is authenticated. Authenticated scans are automatically saved to history.
    """
    product = await off_client.get_product(body.barcode)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in database")
    
    raw_ingredients = product.get("ingredients_text", "").split(",")
    raw_ingredients = [i.strip() for i in raw_ingredients if i.strip()]
    
    user_profile = {"allergies": [], "conditions": [], "goals": []}
    if current_user:
        result = await db.execute(select(User).where(User.id == current_user["uid"]))
        user = result.scalars().first()
        if user:
            user_profile = {
                "user_id": user.id,
                "allergies": user.allergies or [],
                "conditions": user.conditions or [],
                "goals": user.goals or []
            }
    
    analyzed = engine.analyze_ingredients(raw_ingredients, user_profile=user_profile)
    nova_class = int(product.get("nova_group", 4))
    score_data = engine.calculate_hs_score(analyzed, nova_class, user_profile=user_profile)
    
    if current_user:
        history_entry = ScanHistory(
            user_id=current_user["uid"],
            product_name=product.get("product_name", "Unknown"),
            brand=product.get("brands", "Unknown"),
            health_score=score_data["final_score"],
            nova_group=nova_class,
            nutrients=product.get("nutriments", {}),
            ingredients=[i.model_dump() for i in analyzed] if analyzed else []
        )
        db.add(history_entry)
        await db.commit()
    
    return ScanResponse(
        product_name=product.get("product_name", "Unknown"),
        brand=product.get("brands", "Unknown"),
        ingredients=analyzed,
        safety_score=score_data["final_score"],
        nova_class=nova_class,
        breakdown=ScoreBreakdown(**score_data["breakdown"]),
        nutrients=product.get("nutriments", {})
    )
