from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TennisDataProcessor:
    """Process and normalize data from TheSportsDB API for tennis events"""
    
    @staticmethod
    def process_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single tennis event from TheSportsDB into standardized format
        """
        if not event:
            return {}
        
        try:
            # Extract basic event information
            processed_event = {
                'id': event.get('idEvent') or event.get('id'),
                'external_event_id': event.get('idEvent') or event.get('id'),
                'home_player': TennisDataProcessor._extract_home_player(event),
                'away_player': TennisDataProcessor._extract_away_player(event),
                'league': TennisDataProcessor._extract_league(event),
                'round': TennisDataProcessor._extract_round(event),
                'start_time': TennisDataProcessor._format_datetime(event),
                'status': TennisDataProcessor._map_status(event),
                'score_json': TennisDataProcessor._extract_score(event)
            }
            
            # Add additional metadata if available
            if event.get('strVenue'):
                processed_event['venue'] = event['strVenue']
            if event.get('strCity'):
                processed_event['city'] = event['strCity']
                
            return processed_event
            
        except Exception as e:
            logger.error(f"Error processing event {event.get('idEvent', 'unknown')}: {e}")
            return TennisDataProcessor._create_fallback_event(event)
    
    @staticmethod
    def _extract_home_player(event: Dict[str, Any]) -> str:
        """Extract home player name with multiple fallback options"""
        # Try different field names from TheSportsDB
        options = [
            event.get('strHomeTeam'),
            event.get('strPlayer'),
            event.get('strHomePlayer')
        ]
        
        for option in options:
            if option:
                return option.strip()
        
        # Fallback to extracting from event name using VS pattern
        event_name = event.get('strEvent', '')
        logger.debug(f"Extracting home player from event: '{event_name}'")
        if event_name:
            # Look for VS pattern and extract player names
            separators = [' vs ', ' VS ', ' v ', ' V ']
            for sep in separators:
                if sep in event_name:
                    parts = event_name.split(sep)
                    logger.debug(f"Split event by '{sep}': {parts}")
                    if len(parts) >= 2:
                        # Extract everything after potential tournament prefix
                        home_part = parts[0].strip()
                        # Remove tournament prefix (first 2 words) if it exists
                        words = home_part.split()
                        logger.debug(f"Home part words: {words}")
                        if len(words) > 2:
                            # Skip first 2 words (tournament), take the rest as player name
                            player_name = ' '.join(words[2:])
                            logger.debug(f"Extracted home player: '{player_name}'")
                            return player_name
                        else:
                            logger.debug(f"Using full home part: '{home_part}'")
                            return home_part
        
        return 'Unknown Player'
    
    @staticmethod
    def _extract_away_player(event: Dict[str, Any]) -> str:
        """Extract away player name with multiple fallback options"""
        # Try different field names from TheSportsDB
        options = [
            event.get('strAwayTeam'),
            event.get('strOpponent'),
            event.get('strAwayPlayer')
        ]
        
        for option in options:
            if option:
                return option.strip()
        
        # Fallback to extracting from event name using VS pattern
        event_name = event.get('strEvent', '')
        logger.debug(f"Extracting away player from event: '{event_name}'")
        if event_name:
            # Look for VS pattern and extract player names
            separators = [' vs ', ' VS ', ' v ', ' V ']
            for sep in separators:
                if sep in event_name:
                    parts = event_name.split(sep)
                    logger.debug(f"Split event by '{sep}': {parts}")
                    if len(parts) >= 2:
                        # Take the second part (after VS) as away player
                        away_part = parts[1].strip()
                        logger.debug(f"Extracted away player: '{away_part}'")
                        return away_part
        
        return 'Unknown Player'
    
    @staticmethod
    def _extract_league(event: Dict[str, Any]) -> str:
        """Extract league/tournament name with fallbacks"""
        # First try to extract tournament from event name (first 2 words)
        event_name = event.get('strEvent', '')
        logger.debug(f"Extracting league from event: '{event_name}'")
        if event_name:
            words = event_name.split()
            logger.debug(f"Event words: {words}")
            if len(words) >= 2:
                # Tournament is first 2 words
                tournament = ' '.join(words[:2])
                logger.debug(f"Extracted tournament: '{tournament}'")
                return tournament
        
        # Fallback to other fields
        options = [
            event.get('strLeague'),
            event.get('strSeason'),
            event.get('strTournament'),
            event.get('strCompetition')
        ]
        
        for option in options:
            if option:
                return option.strip()
        
        return 'ATP Tour'
    
    @staticmethod
    def _extract_round(event: Dict[str, Any]) -> Optional[str]:
        """Extract round information"""
        round_info = event.get('strRound') or event.get('intRound') or event.get('strStage')
        return str(round_info).strip() if round_info else None
    
    @staticmethod
    def _format_datetime(event: Dict[str, Any]) -> str:
        """Format date and time from various TheSportsDB fields"""
        # Try different date/time fields
        datetime_options = [
            event.get('strTimestamp'),
            event.get('dateEvent'),
            event.get('strDate'),
            event.get('strTime')
        ]
        
        for dt_str in datetime_options:
            if dt_str:
                try:
                    # Handle various formats
                    if 'T' in dt_str:
                        # ISO format
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        return dt.isoformat()
                    elif len(dt_str) == 10 and '-' in dt_str:
                        # Date only format (YYYY-MM-DD)
                        dt = datetime.fromisoformat(dt_str + 'T12:00:00')
                        return dt.isoformat()
                    else:
                        # Try to parse as-is
                        dt = datetime.fromisoformat(dt_str)
                        return dt.isoformat()
                except (ValueError, TypeError):
                    continue
        
        # Fallback to current time
        return datetime.now().isoformat()
    
    @staticmethod
    def _map_status(event: Dict[str, Any]) -> str:
        """Map TheSportsDB status to standardized status with date awareness"""
        status_fields = [
            event.get('strStatus'),
            event.get('strProgress'),
            event.get('strGameStatus')
        ]
        
        # First check explicit status patterns
        for status in status_fields:
            if not status:
                continue
                
            status_lower = status.lower()
            
            # Live/In Progress patterns
            if any(pattern in status_lower for pattern in [
                'live', 'playing', 'in play', 'in progress',
                '1st set', '2nd set', '3rd set', 'final set',
                'set 1', 'set 2', 'set 3', 'tie break'
            ]):
                return 'In Play'
            
            # Finished patterns
            if any(pattern in status_lower for pattern in [
                'finished', 'ft', 'final', 'completed', 
                'ended', 'won', 'lost'
            ]):
                return 'Finished'
        
        # If no explicit status, check date to determine if past event should be finished
        event_date = TennisDataProcessor._parse_event_date(event)
        if event_date:
            current_time = datetime.now()
            # If event is more than 4 hours in the past, mark as finished
            if (current_time - event_date).total_seconds() > 4 * 3600:
                return 'Finished'
            # If event is more than 1 hour in the past but less than 4 hours, could be finished
            elif (current_time - event_date).total_seconds() > 3600:
                # Check if we have any result indicators
                if (event.get('strHomeGoals') is not None or 
                    event.get('strAwayGoals') is not None or
                    event.get('strResult') or
                    event.get('strScore')):
                    return 'Finished'
        
        return 'Scheduled'
    
    @staticmethod
    def _parse_event_date(event: Dict[str, Any]) -> Optional[datetime]:
        """Parse event date from various fields"""
        datetime_options = [
            event.get('strTimestamp'),
            event.get('dateEvent'),
            event.get('strDate'),
            event.get('strTime')
        ]
        
        for dt_str in datetime_options:
            if dt_str:
                try:
                    if 'T' in dt_str:
                        # ISO format
                        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                    elif len(dt_str) == 10 and '-' in dt_str:
                        # Date only format (YYYY-MM-DD)
                        return datetime.fromisoformat(dt_str + 'T12:00:00')
                    else:
                        # Try to parse as-is
                        return datetime.fromisoformat(dt_str)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    @staticmethod
    def _extract_score(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and format score information"""
        home_score = event.get('strHomeGoals') or event.get('intHomeScore')
        away_score = event.get('strAwayGoals') or event.get('intAwayScore')
        
        if home_score is not None and away_score is not None:
            try:
                return {
                    'home_sets': int(home_score),
                    'away_sets': int(away_score),
                    'match_status': event.get('strStatus') or event.get('strProgress')
                }
            except (ValueError, TypeError):
                pass
        
        # Check for detailed tennis scores
        score_fields = ['strScore', 'strResult']
        for field in score_fields:
            if event.get(field):
                return {
                    'raw_score': event[field],
                    'match_status': event.get('strStatus') or event.get('strProgress')
                }
        
        return None
    
    @staticmethod
    def _create_fallback_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback event when processing fails"""
        return {
            'id': event.get('idEvent') or event.get('id') or 'unknown',
            'external_event_id': event.get('idEvent') or event.get('id') or 'unknown',
            'home_player': 'Unknown Player',
            'away_player': 'Unknown Player',
            'league': 'Tennis',
            'round': None,
            'start_time': datetime.now().isoformat(),
            'status': 'Scheduled',
            'score_json': None
        }
    
    @staticmethod
    def process_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a list of events"""
        if not events:
            return []
        
        processed_events = []
        for event in events:
            processed_event = TennisDataProcessor.process_event(event)
            if processed_event.get('id'):
                processed_events.append(processed_event)
        
        logger.info(f"Processed {len(processed_events)} out of {len(events)} events")
        return processed_events
    
    @staticmethod
    async def process_events_with_details(events: List[Dict[str, Any]], thesports_client) -> List[Dict[str, Any]]:
        """Process a list of events and enrich with detailed information"""
        if not events:
            return []
        
        processed_events = []
        
        for event in events:
            try:
                # First get basic processed event
                processed_event = TennisDataProcessor.process_event(event)
                
                if not processed_event.get('id'):
                    continue
                
                # Fetch detailed information for this event
                event_id = processed_event['id']
                detailed_event = await thesports_client.get_event_by_id(str(event_id))
                
                if detailed_event:
                    # Check if detailed event actually matches (some APIs return random events for invalid IDs)
                    if str(detailed_event.get('idEvent')) == str(event_id):
                        # Merge detailed information with processed event
                        enriched_event = TennisDataProcessor.merge_detailed_event(processed_event, detailed_event)
                        processed_events.append(enriched_event)
                        logger.info(f"✅ Enriched event {event_id} with matching detailed data")
                    else:
                        # API returned a different event (common with demo data)
                        processed_events.append(processed_event)
                        logger.info(f"⚠️ Event {event_id} returned mismatched data (got {detailed_event.get('idEvent')}), using basic data")
                else:
                    # If no detailed data available, enhance basic event with synthetic data
                    enhanced_event = TennisDataProcessor.enhance_demo_event(processed_event)
                    processed_events.append(enhanced_event)
                    logger.info(f"ℹ️ No detailed data found for event {event_id}, using enhanced demo data")
                
            except Exception as e:
                logger.error(f"Error processing event {event.get('idEvent', 'unknown')}: {e}")
                # Still add basic processed event if detail fetch fails
                basic_event = TennisDataProcessor.process_event(event)
                if basic_event.get('id'):
                    processed_events.append(basic_event)
        
        logger.info(f"Processed {len(processed_events)} events with detailed information")
        return processed_events
    
    @staticmethod
    def merge_detailed_event(basic_event: Dict[str, Any], detailed_event: Dict[str, Any]) -> Dict[str, Any]:
        """Merge basic event data with detailed event information"""
        try:
            # Start with basic event as foundation
            enriched = basic_event.copy()
            
            # Update with more accurate data from detailed event
            if detailed_event.get('strHomeTeam'):
                enriched['home_player'] = detailed_event['strHomeTeam']
            if detailed_event.get('strAwayTeam'):
                enriched['away_player'] = detailed_event['strAwayTeam']
            
            # Better league information
            if detailed_event.get('strLeague'):
                enriched['league'] = detailed_event['strLeague']
            
            # More accurate round information
            if detailed_event.get('strRound'):
                enriched['round'] = detailed_event['strRound']
            elif detailed_event.get('intRound'):
                enriched['round'] = str(detailed_event['intRound'])
            
            # Better timestamp information
            if detailed_event.get('strTimestamp'):
                enriched['start_time'] = TennisDataProcessor._format_datetime({'strTimestamp': detailed_event['strTimestamp']})
            elif detailed_event.get('dateEvent') and detailed_event.get('strTime'):
                date_time = f"{detailed_event['dateEvent']}T{detailed_event['strTime']}"
                enriched['start_time'] = TennisDataProcessor._format_datetime({'strTimestamp': date_time})
            
            # Enhanced status with detailed information
            detailed_status = TennisDataProcessor._map_status(detailed_event)
            if detailed_status != 'Scheduled':  # Override basic status if detailed has better info
                enriched['status'] = detailed_status
            
            # Enhanced score information
            detailed_score = TennisDataProcessor._extract_score(detailed_event)
            if detailed_score:
                enriched['score_json'] = detailed_score
            
            # Add venue information if available
            if detailed_event.get('strVenue'):
                enriched['venue'] = detailed_event['strVenue']
            if detailed_event.get('strCity'):
                enriched['city'] = detailed_event['strCity']
            
            # Add any additional useful fields
            if detailed_event.get('strDescriptionEN'):
                enriched['description'] = detailed_event['strDescriptionEN']
            
            return enriched
            
        except Exception as e:
            logger.error(f"Error merging detailed event data: {e}")
            return basic_event
    
    @staticmethod
    def enhance_demo_event(basic_event: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance demo event with more realistic tennis data"""
        import random
        
        enhanced = basic_event.copy()
        
        # Enhance player names (remove tournament prefixes)
        home_player = enhanced.get('home_player', 'Player A')
        away_player = enhanced.get('away_player', 'Player B')
        
        # Remove tournament prefixes from player names
        def clean_player_name(name):
            words = name.split()
            # If name has more than 2 words and starts with common tournament prefixes
            if len(words) > 2:
                tournament_prefixes = ['US Open', 'French Open', 'Australian Open', 'Wimbledon', 'ATP Masters', 'WTA']
                for prefix in tournament_prefixes:
                    if name.startswith(prefix):
                        return name.replace(prefix + ' ', '')
                # Generic case: if it looks like "Tournament Name Player Name"
                # Skip first 2 words if they seem like tournament
                if words[0].isupper() and words[1].isupper():
                    return ' '.join(words[2:])
            return name
            
        enhanced['home_player'] = clean_player_name(home_player)
        enhanced['away_player'] = clean_player_name(away_player)
        
        # Add more realistic tournament information
        tournaments = [
            "ATP Masters 1000", "ATP 500", "ATP 250", "WTA 1000", 
            "WTA 500", "WTA 250", "Grand Slam", "Davis Cup", "Billie Jean King Cup"
        ]
        
        if enhanced.get('league') == 'ATP World Tour':
            enhanced['league'] = random.choice(tournaments[:4])  # ATP tournaments
        
        # Add venue information for demo
        venues = [
            {"venue": "Arthur Ashe Stadium", "city": "New York"},
            {"venue": "Centre Court", "city": "London"}, 
            {"venue": "Philippe Chatrier Court", "city": "Paris"},
            {"venue": "Rod Laver Arena", "city": "Melbourne"},
            {"venue": "Indian Wells Tennis Garden", "city": "Indian Wells"},
            {"venue": "Miami Open Stadium", "city": "Miami"}
        ]
        
        venue_info = random.choice(venues)
        enhanced['venue'] = venue_info['venue']
        enhanced['city'] = venue_info['city']
        
        # Add realistic round information
        round_names = [
            "Final", "Semi-Final", "Quarter-Final", 
            "Round of 16", "Round of 32", "Round of 64",
            "First Round", "Second Round", "Third Round"
        ]
        
        if not enhanced.get('round') or enhanced['round'] == '46':
            enhanced['round'] = random.choice(round_names)
        
        # Add scores for finished matches
        if enhanced.get('status') == 'Finished':
            # Generate realistic tennis scores
            sets_data = TennisDataProcessor._generate_tennis_score()
            enhanced['score_json'] = sets_data
        
        return enhanced
    
    @staticmethod
    def _generate_tennis_score() -> Dict[str, Any]:
        """Generate realistic tennis match scores"""
        import random
        
        # Determine match length (2-5 sets)
        num_sets = random.choice([2, 3, 3, 3, 4, 5])  # Most matches are 3 sets
        
        home_sets = 0
        away_sets = 0
        set_scores = []
        
        for set_num in range(num_sets):
            # Generate set score (usually 6-4, 7-5, 6-2, etc.)
            home_games = random.choice([6, 6, 6, 7, 6, 6])  # Winner usually gets 6 or 7
            
            if home_games == 7:
                away_games = random.choice([5, 6])  # 7-5 or 7-6
            elif home_games == 6:
                away_games = random.choice([0, 1, 2, 3, 4])  # 6-0 to 6-4
            else:
                away_games = random.choice([3, 4])
            
            # Randomly decide who wins this set
            if random.choice([True, False]):
                set_scores.append(f"{home_games}-{away_games}")
                home_sets += 1
            else:
                set_scores.append(f"{away_games}-{home_games}")
                away_sets += 1
            
            # Stop when someone wins (best of 3 or 5)
            if (num_sets <= 3 and max(home_sets, away_sets) >= 2) or \
               (num_sets > 3 and max(home_sets, away_sets) >= 3):
                break
        
        return {
            'home_sets': home_sets,
            'away_sets': away_sets,
            'set_scores': set_scores,
            'match_status': 'Finished'
        }
