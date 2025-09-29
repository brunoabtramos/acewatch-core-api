from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.models import User, Favorite, Alert
from app.schemas import (
    UserCreate, 
    FavoriteCreate, AlertCreate, AlertUpdate
)
from app.auth import get_password_hash, verify_password, create_access_token

# User CRUD operations
def create_user(db: Session, user: UserCreate):
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise ValueError("Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# Match CRUD operations removed - data now comes directly from TheSportsDB API

# Favorite CRUD operations
def create_favorite(db: Session, favorite: FavoriteCreate, user_id: int):
    # Check if favorite already exists
    query = db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.type == favorite.type)
    
    if favorite.type == "player" and favorite.external_player_id:
        query = query.filter(Favorite.external_player_id == favorite.external_player_id)
    elif favorite.type == "match" and favorite.external_event_id:
        query = query.filter(Favorite.external_event_id == favorite.external_event_id)
    
    existing_favorite = query.first()
    if existing_favorite:
        return existing_favorite
    
    db_favorite = Favorite(
        user_id=user_id,
        external_player_id=favorite.external_player_id,
        external_event_id=favorite.external_event_id,
        type=favorite.type
    )
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite

def get_user_favorites(db: Session, user_id: int):
    return db.query(Favorite).filter(Favorite.user_id == user_id).all()

def delete_favorite(db: Session, favorite_id: int, user_id: int):
    db_favorite = db.query(Favorite).filter(
        Favorite.id == favorite_id, 
        Favorite.user_id == user_id
    ).first()
    if not db_favorite:
        return False
    
    db.delete(db_favorite)
    db.commit()
    return True

# Alert CRUD operations
def create_alert(db: Session, alert: AlertCreate, user_id: int):
    # Check if alert already exists for this user and event with the same trigger
    existing_alert = db.query(Alert).filter(
        Alert.user_id == user_id,
        Alert.external_event_id == alert.external_event_id,
        Alert.trigger == alert.trigger
    ).first()
    
    if existing_alert:
        return existing_alert
    
    db_alert = Alert(
        user_id=user_id,
        external_event_id=alert.external_event_id,
        trigger=alert.trigger
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

def get_user_alerts(db: Session, user_id: int):
    return db.query(Alert).filter(Alert.user_id == user_id).all()

def update_alert(db: Session, alert_id: int, alert_update: AlertUpdate, user_id: int):
    db_alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user_id
    ).first()
    
    if not db_alert:
        return None
    
    if alert_update.trigger is not None:
        db_alert.trigger = alert_update.trigger
    if alert_update.is_active is not None:
        db_alert.is_active = alert_update.is_active
    
    db.commit()
    db.refresh(db_alert)
    return db_alert

def delete_alert(db: Session, alert_id: int, user_id: int):
    db_alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user_id
    ).first()
    
    if not db_alert:
        return False
    
    db.delete(db_alert)
    db.commit()
    return True

# Utility functions for matches removed - data now comes directly from TheSportsDB API
