from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PlanCreateRequest(BaseModel):
    user_name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=12, le=120)
    gender: str = Field(...)
    height: Optional[float] = Field(None, ge=50, le=250)
    weight: Optional[float] = Field(None, ge=20, le=300)
    fitness_goal: str = Field(...)
    fitness_level: str = Field(...)
    workout_location: str = Field(...)
    available_equipment: Optional[str] = "Standard Gym Equipment"
    days_per_week: int = Field(7, ge=1, le=7)
    injuries_limitations: Optional[str] = "None"
    dietary_preference: Optional[str] = "Balanced"

class FeedbackRequest(BaseModel):
    feedback: str = Field(..., min_length=3, max_length=2000)

class PlanResponse(BaseModel):
    id: int
    user_name: str
    age: int
    gender: str
    height: Optional[float]
    weight: Optional[float]
    fitness_goal: str
    fitness_level: str
    workout_location: str
    available_equipment: Optional[str]
    days_per_week: int
    injuries_limitations: Optional[str]
    dietary_preference: Optional[str]
    original_workout_plan: str
    nutrition_tips: str
    recovery_tips: str
    user_feedback: Optional[str]
    updated_workout_plan: Optional[str]
    feedback_applied: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
