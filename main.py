from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn
import os
import logging

logger = logging.getLogger(__name__)

from app.database import get_db, engine, Base
from app.auth import verify_token, get_current_user
from app.models import User, Favorite, Alert
from app.thesportsdb import TheSportsDBClient
from app.data_processor import TennisDataProcessor
from app.schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    FavoriteCreate, FavoriteResponse,
    AlertCreate, AlertUpdate, AlertResponse
)
from app.crud import (
    create_user, authenticate_user, create_access_token,
    create_favorite, get_user_favorites, delete_favorite,
    create_alert, update_alert, delete_alert, get_user_alerts
)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AceWatch Core API", version="1.0.0")

# TheSportsDB client
thesports_client = TheSportsDBClient(api_key=os.getenv("SPORTSDB_API_KEY", "276863"))

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Auth routes
@app.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user)
    return db_user

@app.post("/auth/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Match routes removed - now using real-time tennis endpoints

# Favorite routes (POST and DELETE - satisfies requirements)
@app.post("/favorites", response_model=FavoriteResponse)
def add_favorite(
    favorite: FavoriteCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_favorite(db, favorite, current_user.id)

@app.get("/favorites", response_model=List[FavoriteResponse])
def get_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_user_favorites(db, current_user.id)

@app.delete("/favorites/{favorite_id}")
def remove_favorite(
    favorite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = delete_favorite(db, favorite_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"message": "Favorite removed successfully"}

# Alert routes (PUT - satisfies requirement)
@app.post("/alerts", response_model=AlertResponse)
def create_alert_endpoint(
    alert: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_alert(db, alert, current_user.id)

@app.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_user_alerts(db, current_user.id)

@app.put("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert_endpoint(
    alert_id: int,
    alert: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated_alert = update_alert(db, alert_id, alert, current_user.id)
    if not updated_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return updated_alert

@app.delete("/alerts/{alert_id}")
def delete_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = delete_alert(db, alert_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted successfully"}

# WebSocket endpoint for live updates
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except Exception as e:
        manager.disconnect(websocket)

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "debug-v2"}

@app.get("/test-extraction")
async def test_extraction():
    """Test endpoint to verify our extraction logic"""
    print("🧪 TEST EXTRACTION ENDPOINT CALLED")
    test_event = {
        'strEvent': 'US Open Sinner vs Alcaraz',
        'strLeague': 'ATP World Tour'
    }
    
    home_player = TennisDataProcessor._extract_home_player(test_event)
    away_player = TennisDataProcessor._extract_away_player(test_event)
    league = TennisDataProcessor._extract_league(test_event)
    
    return {
        "raw_event": test_event['strEvent'],
        "extracted": {
            "home_player": home_player,
            "away_player": away_player, 
            "league": league
        }
    }

# ==========================================
# LIVE TENNIS DATA (Direct from TheSportsDB)  
# ==========================================

@app.get("/tennis/live")
async def get_live_tennis_events():
    """Get live tennis events with basic processing"""
    try:
        raw_events = await thesports_client.get_live_events()
        processed_events = TennisDataProcessor.process_events(raw_events or [])
        return {
            "data": processed_events,
            "count": len(processed_events),
            "source": "live"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching live events: {str(e)}")

@app.get("/tennis/upcoming")  
async def get_upcoming_tennis_events(league_id: str = "4464"):
    """Get upcoming tennis events with multiple fallback strategies"""
    try:
        all_upcoming = []
        
        # Get upcoming events from TheSportsDB
        raw_events = await thesports_client.get_next_events(league_id="4464")
        all_upcoming = raw_events or []
        
        # Process events with basic processing (no individual API calls)
        processed_events = TennisDataProcessor.process_events(all_upcoming)
        
        return {
            "data": processed_events,
            "count": len(processed_events),
            "source": "upcoming"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching upcoming events: {str(e)}")

@app.get("/tennis/recent")
async def get_recent_tennis_events():
    """Get recent/finished tennis events with proper date filtering"""
    try:
        # Get recent/previous events from TheSportsDB
        raw_events = await thesports_client._get_previous_events_fallback()
        all_recent = raw_events or []
        
        # Process events with basic processing (no individual API calls)
        processed_events = TennisDataProcessor.process_events(all_recent)
        
        return {
            "data": processed_events[:20],  # Limit to 20 most recent
            "count": len(processed_events[:20]), 
            "source": "recent"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent events: {str(e)}")

@app.get("/tennis/event/{event_id}")
async def get_tennis_event_details(event_id: str):
    """Get specific tennis event details"""
    try:
        event = await thesports_client.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"data": event}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching event: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
