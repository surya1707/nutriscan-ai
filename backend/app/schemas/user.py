from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class UserProfileBase(BaseModel):
    allergies: Optional[List[str]] = []
    conditions: Optional[List[str]] = []
    goals: Optional[List[str]] = []
    display_name: Optional[str] = None

class UserProfileResponse(UserProfileBase):
    id: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "abc123xyz",
                "allergies": ["peanuts", "dairy"],
                "conditions": ["Diabetes"],
                "goals": ["weight loss"],
                "display_name": "Alex"
            }
        }
    )

class UserProfileUpdateRequest(BaseModel):
    allergies: Optional[List[str]] = None
    conditions: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    display_name: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "allergies": ["peanuts", "dairy"],
                "conditions": ["Diabetes"],
                "goals": ["weight loss"],
                "display_name": "Alex"
            }
        }
    )
