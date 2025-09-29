from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Match schemas removed - data now comes directly from TheSportsDB API

# Favorite schemas
class FavoriteBase(BaseModel):
    type: str  # "player" or "match"

class FavoriteCreate(FavoriteBase):
    external_player_id: Optional[str] = None
    external_event_id: Optional[str] = None
    # match_id removed - using external_event_id for direct API reference

class FavoriteResponse(FavoriteBase):
    id: int
    user_id: int
    external_player_id: Optional[str] = None
    external_event_id: Optional[str] = None
    # match_id removed - using external_event_id for direct API reference
    created_at: datetime
    
    class Config:
        from_attributes = True

# Alert schemas
class AlertBase(BaseModel):
    trigger: str  # "match_started", "tie_break", "third_set", "match_finished"

class AlertCreate(AlertBase):
    external_event_id: str  # Direct reference to TheSportsDB event

class AlertUpdate(BaseModel):
    trigger: Optional[str] = None
    is_active: Optional[bool] = None

class AlertResponse(AlertBase):
    id: int
    user_id: int
    external_event_id: str  # Direct reference to TheSportsDB event
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
