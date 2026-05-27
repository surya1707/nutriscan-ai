from pydantic import BaseModel
from typing import List, Optional, Dict

class IngredientRequest(BaseModel):
    ingredients: List[str]
    user_id: Optional[str] = None

class BarcodeRequest(BaseModel):
    barcode: str
    user_id: Optional[str] = None

class IngredientResult(BaseModel):
    name: str
    status: str  # safe, caution, danger
    reason: str

class ScoreBreakdown(BaseModel):
    allergenDeduction: float
    novaDeduction: float
    additiveDeduction: float
    conditionDeduction: float

class ScanResponse(BaseModel):
    product_name: Optional[str] = "Scanned Label"
    brand: Optional[str] = "Unknown"
    ingredients: List[IngredientResult]
    safety_score: int
    nova_class: int
    breakdown: ScoreBreakdown
    nutrients: Optional[Dict] = None
