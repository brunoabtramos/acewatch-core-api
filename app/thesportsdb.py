import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TheSportsDBClient:
    """Client for TheSportsDB API"""
    
    def __init__(self, api_key: str = "276863"):
        self.api_key = api_key
        self.base_url = "https://www.thesportsdb.com/api/v2/json"
        # v2 API uses X-API-KEY header for authentication
        headers = {"X-API-KEY": api_key}
        self.client = httpx.AsyncClient(timeout=30.0, verify=False, headers=headers)
    
    async def get_events_by_date(self, date: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get tennis events for a specific date using v1 API (more reliable for date-based queries)
        """
        try:
            # Use v1 API for date-based queries which is more reliable
            v1_base_url = "https://www.thesportsdb.com/api/v1/json/3"  # Free tier
            url = f"{v1_base_url}/eventsday.php?d={date}&s=Tennis"
            
            logger.info(f"Fetching tennis events for date {date} from TheSportsDB v1")
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            events = data.get('events', [])
            
            tennis_events = []
            if events:
                for event in events:
                    # Filter for tennis events
                    if event.get('strSport', '').lower() == 'tennis':
                        tennis_events.append(event)
            
            logger.info(f"Found {len(tennis_events)} tennis events for {date}")
            return tennis_events
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching events for {date}: {e}")
            # Fallback to previous API
            return await self._get_previous_events_fallback()
        except Exception as e:
            logger.error(f"Error fetching events for {date}: {e}")
            return await self._get_previous_events_fallback()
    
    async def _get_previous_events_fallback(self) -> Optional[List[Dict[str, Any]]]:
        """Fallback method to get previous events when date-based query fails"""
        try:
            url = f"{self.base_url}/schedule/previous/league/4464"
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            events = data.get('schedule', data.get('events', []))
            
            logger.info(f"Fallback: Found {len(events) if events else 0} previous tennis events")
            return events or []
            
        except Exception as e:
            logger.error(f"Fallback also failed: {e}")
            return []
    
    async def get_live_events(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get live tennis events using v2 API
        """
        try:
            # v2 API route for live events by sport
            url = f"{self.base_url}/livescore/Tennis"
            
            logger.info("Fetching live tennis events from TheSportsDB v2")
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            # v2 API response structure for livescores
            events = data.get('livescore', data.get('events', []))
            
            tennis_events = []
            if events:
                for event in events:
                    tennis_events.append(event)  # Already tennis events from tennis endpoint
            
            logger.info(f"Found {len(tennis_events)} live tennis events")
            return tennis_events
            
        except Exception as e:
            logger.error(f"Error fetching live events: {e}")
            return None
    
    async def get_next_events(self, league_id: str = "4464") -> Optional[List[Dict[str, Any]]]:
        """
        Get next tennis events using v2 API
        Default to ATP Tour (ID: 4464), but can specify other tennis leagues
        """
        try:
            # v2 API route for next events by league
            url = f"{self.base_url}/schedule/next/league/{league_id}"
                
            logger.info(f"Fetching next ATP events for league {league_id} from TheSportsDB v2")
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            # v2 API response structure for schedule
            events = data.get('schedule', data.get('events', []))
            
            tennis_events = []
            if events:
                for event in events:
                    tennis_events.append(event)  # Already tennis events from tennis league
                        
            logger.info(f"Found {len(tennis_events)} upcoming tennis events")
            return tennis_events
            
        except Exception as e:
            logger.error(f"Error fetching next events: {e}")
            return None
    
    async def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get specific event details by ID with fallback strategies"""
        try:
            # Try v1 API first (more reliable for detailed lookups)
            v1_base_url = "https://www.thesportsdb.com/api/v1/json/3"
            url = f"{v1_base_url}/lookupevent.php?id={event_id}"
            
            logger.info(f"Fetching event details for ID {event_id} from TheSportsDB v1")
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            events = data.get('events', [])
            
            if events and events[0]:
                event_data = events[0]
                # Verify this is actually the event we requested (not random demo data)
                if str(event_data.get('idEvent')) == str(event_id):
                    logger.info(f"✅ Found matching detailed event data for {event_id}")
                    return event_data
                else:
                    logger.warning(f"⚠️ API returned different event {event_data.get('idEvent')} for requested {event_id}")
                    return None
            
            # Fallback to v2 API
            logger.info(f"V1 failed, trying v2 for event {event_id}")
            url_v2 = f"{self.base_url}/lookup/event"
            params = {'id': event_id}
            
            response = await self.client.get(url_v2, params=params)
            response.raise_for_status()
            
            data = response.json()
            events = data.get('events', [])
            
            return events[0] if events else None
            
        except Exception as e:
            logger.error(f"Error fetching event {event_id}: {e}")
            return None
    
    async def search_players(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Search for players by name"""
        try:
            url = f"{self.base_url}/search/players"
            params = {'query': query, 'sport': 'Tennis'}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            players = data.get('player', [])
            
            # Filter tennis players
            tennis_players = []
            if players:
                for player in players:
                    if player and player.get('strSport', '').lower() == 'tennis':
                        tennis_players.append(player)
            
            return tennis_players
            
        except Exception as e:
            logger.error(f"Error searching players: {e}")
            return None
    
    async def get_player_by_id(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get player details by ID"""
        try:
            url = f"{self.base_url}/lookup/player"
            params = {'id': player_id}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            players = data.get('players', [])
            
            return players[0] if players else None
            
        except Exception as e:
            logger.error(f"Error fetching player {player_id}: {e}")
            return None
    
    async def get_leagues(self) -> Optional[List[Dict[str, Any]]]:
        """Get tennis leagues"""
        try:
            url = f"{self.base_url}/all/leagues"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            all_leagues = data.get('leagues', [])
            
            # Filter tennis leagues
            tennis_leagues = []
            if all_leagues:
                for league in all_leagues:
                    if league and league.get('strSport', '').lower() == 'tennis':
                        tennis_leagues.append(league)
            
            return tennis_leagues
            
        except Exception as e:
            logger.error(f"Error fetching leagues: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
