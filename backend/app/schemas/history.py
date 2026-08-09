from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime

class ScanHistoryBase(BaseModel):
    product_name: Optional[str] = None
    brand: Optional[str] = None
    health_score: Optional[int] = None
    nova_group: Optional[int] = None
    nutrients: Optional[Any] = None
    ingredients: Optional[Any] = None

class ScanHistoryCreateRequest(ScanHistoryBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_name": "Coca Cola",
                "brand": "Coca-Cola",
                "health_score": 25,
                "nova_group": 4,
                "nutrients": {"sugars": 10.6},
                "ingredients": ["Carbonated Water", "High Fructose Corn Syrup", "Caramel Color"]
            }
        }
    )

class ScanHistoryResponse(ScanHistoryBase):
    id: int
    user_id: str
    scanned_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": "abc123xyz",
                "scanned_at": "2024-05-15T12:00:00Z",
                "product_name": "Coca Cola",
                "brand": "Coca-Cola",
                "health_score": 25,
                "nova_group": 4,
                "nutrients": {"sugars": 10.6},
                "ingredients": ["Carbonated Water", "High Fructose Corn Syrup", "Caramel Color"]
            }
        }
    )
