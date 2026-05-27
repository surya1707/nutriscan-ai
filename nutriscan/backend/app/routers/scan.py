from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from ..schemas.scan import IngredientRequest, BarcodeRequest, ScanResponse, IngredientResult, ScoreBreakdown
from ..services.ingredient_engine import IngredientEngine
from ..services.nova_classifier import NovaClassifier
from ..services.off_client import OpenFoodFactsClient

router = APIRouter(prefix="/scan", tags=["scan"])

engine = IngredientEngine()
nova_classifier = NovaClassifier()
off_client = OpenFoodFactsClient()

@router.post("/analyse", response_model=ScanResponse)
async def analyse_ingredients(request: IngredientRequest):
    # In a real app, we would fetch user profile from DB using request.user_id
    # For now, we use a mock profile or empty
    mock_profile = {"allergies": [], "conditions": []} 
    
    analyzed = engine.analyze_ingredients(request.ingredients, user_profile=mock_profile)
    nova_class = nova_classifier.classify(request.ingredients)
    score_data = engine.calculate_hs_score(analyzed, nova_class, user_profile=mock_profile)
    
    return ScanResponse(
        ingredients=analyzed,
        safety_score=score_data["final_score"],
        nova_class=nova_class,
        breakdown=ScoreBreakdown(**score_data["breakdown"])
    )

@router.post("/barcode", response_model=ScanResponse)
async def analyse_barcode(request: BarcodeRequest):
    product = await off_client.get_product(request.barcode)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in database")
    
    raw_ingredients = product.get("ingredients_text", "").split(",")
    raw_ingredients = [i.strip() for i in raw_ingredients if i.strip()]
    
    mock_profile = {"allergies": [], "conditions": []}
    
    analyzed = engine.analyze_ingredients(raw_ingredients, user_profile=mock_profile)
    nova_class = int(product.get("nova_group", 4))
    score_data = engine.calculate_hs_score(analyzed, nova_class, user_profile=mock_profile)
    
    return ScanResponse(
        product_name=product.get("product_name", "Unknown"),
        brand=product.get("brands", "Unknown"),
        ingredients=analyzed,
        safety_score=score_data["final_score"],
        nova_class=nova_class,
        breakdown=ScoreBreakdown(**score_data["breakdown"]),
        nutrients=product.get("nutriments", {})
    )
