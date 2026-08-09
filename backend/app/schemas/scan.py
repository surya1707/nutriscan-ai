from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict

class IngredientRequest(BaseModel):
    ingredients: List[str]
    user_id: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingredients": ["water", "sugar", "E621", "palm oil"]
            }
        }
    )

class BarcodeRequest(BaseModel):
    barcode: str
    user_id: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "barcode": "3017620422003"
            }
        }
    )

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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_name": "Example Snack",
                "brand": "SnackCorp",
                "ingredients": [
                    {"name": "water", "status": "safe", "reason": "No major concerns found."},
                    {"name": "E621", "status": "caution", "reason": "Monosodium glutamate: Flavor enhancer; sensitivity concerns."}
                ],
                "safety_score": 85,
                "nova_class": 4,
                "breakdown": {
                    "allergenDeduction": 0,
                    "novaDeduction": 10,
                    "additiveDeduction": 5,
                    "conditionDeduction": 0
                }
            }
        }
    )
