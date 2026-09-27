from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime
from database import Base

class FitnessPlan(Base):
    __tablename__ = "fitness_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User Profile Information
    user_name = Column(String(100), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    height = Column(Float, nullable=True) # in cm
    weight = Column(Float, nullable=True) # in kg
    
    # Fitness Profile & Goals
    fitness_goal = Column(String(100), nullable=False)
    fitness_level = Column(String(50), nullable=False)
    workout_location = Column(String(100), nullable=False)
    available_equipment = Column(String(200), nullable=True)
    days_per_week = Column(Integer, default=7)
    injuries_limitations = Column(Text, nullable=True, default="None")
    dietary_preference = Column(String(100), nullable=True, default="Balanced")
    
    # AI-Generated Content
    original_workout_plan = Column(Text, nullable=False)
    nutrition_tips = Column(Text, nullable=False)
    recovery_tips = Column(Text, nullable=False)
    
    # Feedback & Adaptive Update Storage
    user_feedback = Column(Text, nullable=True)
    updated_workout_plan = Column(Text, nullable=True)
    feedback_applied = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FitnessPlan id={self.id} user='{self.user_name}' goal='{self.fitness_goal}'>"
