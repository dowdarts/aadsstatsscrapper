"""
AADS Database Manager - Supabase Version
Handles player statistics, tournament tracking, and all data operations with Supabase
Created: 2025-12-29
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from supabase import create_client, Client
from difflib import SequenceMatcher

# Supabase configuration
SUPABASE_URL = "https://nelkwitsvxufhyvfgdjq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5lbGt3aXRzdnh1Zmh5dmZnZGpxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5NzMyMTMsImV4cCI6MjA4MjU0OTIxM30.apupa3eCo1aUWAeVF6LsWU3HD04LKz84Adynr4u32TM"

# Service role key from environment (for write operations)
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', SUPABASE_ANON_KEY)


class AADSDataManager:
    """
    Manages AADS tournament data using Supabase as the backend.
    
    Key Features:
    - Complete tournament management (series, events, matches)
    - Player profile management with photos
    - Auto-calculation of derived stats
    - Edit history tracking
    - Version management for auto-refresh
    - Smart player matching across events
    """
    
    def __init__(self, use_service_key: bool = True):
        """
        Initialize the database manager with Supabase client.
        
        Args:
            use_service_key: If True, use service_role key for write access
        """
        key = SUPABASE_SERVICE_KEY if use_service_key else SUPABASE_ANON_KEY
        self.supabase: Client = create_client(SUPABASE_URL, key)
        self.use_service_key = use_service_key
    
    # ========================================================================
    # PLAYER MANAGEMENT
    # ========================================================================
    
    def create_player(self, player_data: Dict) -> str:
        """
        Create a new player profile.
        
        Args:
            player_data: Dictionary with keys: name, nickname, age, hometown, photo_base64
        
        Returns:
            UUID of created player
        """
        payload = {
            'name': player_data.get('name'),
            'nickname': player_data.get('nickname'),
            'age': player_data.get('age'),
            'hometown': player_data.get('hometown'),
            'photo_base64': player_data.get('photo_base64')
        }
        
        result = self.supabase.table('players').insert(payload).execute()
        player_id = result.data[0]['id']
        
        # Create dart setup if provided
        dart_setup = player_data.get('dart_setup')
        if dart_setup:
            self.update_player_dart_setup(player_id, dart_setup)
        
        return player_id
    
    def update_player_profile(self, player_id: str, player_data: Dict):
        """
        Update existing player profile.
        
        Args:
            player_id: UUID of player
            player_data: Dictionary with updated fields
        """
        payload = {}
        for key in ['name', 'nickname', 'age', 'hometown', 'photo_base64']:
            if key in player_data:
                payload[key] = player_data[key]
        
        if payload:
            self.supabase.table('players').update(payload).eq('id', player_id).execute()
        
        # Update dart setup if provided
        if 'dart_setup' in player_data:
            self.update_player_dart_setup(player_id, player_data['dart_setup'])
    
    def update_player_dart_setup(self, player_id: str, dart_setup: Dict):
        """
        Update or create player's dart setup.
        
        Args:
            player_id: UUID of player
            dart_setup: Dictionary with barrel, shaft, flight, weight, details
        """
        # Check if setup exists
        existing = self.supabase.table('player_dart_setup')\
            .select('id')\
            .eq('player_id', player_id)\
            .execute()
        
        payload = {
            'player_id': player_id,
            'barrel': dart_setup.get('barrel'),
            'shaft': dart_setup.get('shaft'),
            'flight': dart_setup.get('flight'),
            'weight': dart_setup.get('weight'),
            'details': dart_setup.get('details')
        }
        
        if existing.data:
            # Update existing
            self.supabase.table('player_dart_setup')\
                .update(payload)\
                .eq('player_id', player_id)\
                .execute()
        else:
            # Insert new
            self.supabase.table('player_dart_setup').insert(payload).execute()
    
    def get_player(self, player_id: str) -> Optional[Dict]:
        """
        Get player profile with dart setup.
        
        Args:
            player_id: UUID of player
        
        Returns:
            Player data dictionary or None
        """
        result = self.supabase.table('players')\
            .select('*, player_dart_setup(*)')\
            .eq('id', player_id)\
            .execute()
        
        if result.data:
            return result.data[0]
        return None
    
    def get_all_players(self) -> List[Dict]:
        """
        Get all players with their dart setups.
        
        Returns:
            List of player dictionaries
        """
        result = self.supabase.table('players')\
            .select('*, player_dart_setup(*)')\
            .execute()
        
        return result.data
    
    def smart_match_player(self, name: str, threshold: float = 0.8) -> Optional[str]:
        """
        Find existing player by fuzzy name matching.
        
        Args:
            name: Player name to search for
            threshold: Similarity threshold (0-1)
        
        Returns:
            Player UUID if found, None otherwise
        """
        all_players = self.get_all_players()
        
        best_match = None
        best_score = 0
        
        for player in all_players:
            score = SequenceMatcher(None, name.lower(), player['name'].lower()).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = player['id']
        
        return best_match
    
    def get_or_create_player(self, player_data: Dict) -> str:
        """
        Smart player matching: find existing or create new.
        
        Args:
            player_data: Player info dictionary
        
        Returns:
            Player UUID
        """
        name = player_data.get('name')
        
        # Try to find existing player
        existing_id = self.smart_match_player(name, threshold=0.85)
        
        if existing_id:
            # Update existing player
            self.update_player_profile(existing_id, player_data)
            return existing_id
        else:
            # Create new player
            return self.create_player(player_data)
    
    # ========================================================================
    # SERIES AND EVENTS MANAGEMENT
    # ========================================================================
    
    def create_series(self, series_name: str, year: int) -> str:
        """
        Create a new series.
        
        Args:
            series_name: Name of series (e.g., "Series 1")
            year: Year of series
        
        Returns:
            UUID of created series
        """
        payload = {
            'name': series_name,
            'year': year
        }
        
        result = self.supabase.table('series').insert(payload).execute()
        return result.data[0]['id']
    
    def get_or_create_series(self, series_name: str, year: int) -> str:
        """
        Get existing series or create new one.
        
        Args:
            series_name: Name of series
            year: Year of series
        
        Returns:
            Series UUID
        """
        # Try to find existing
        result = self.supabase.table('series')\
            .select('id')\
            .eq('name', series_name)\
            .eq('year', year)\
            .execute()
        
        if result.data:
            return result.data[0]['id']
        else:
            return self.create_series(series_name, year)
    
    def get_all_series(self) -> List[Dict]:
        """Get all series."""
        result = self.supabase.table('series').select('*').execute()
        return result.data
    
    # ========================================================================
    # TOURNAMENT MANAGEMENT
    # ========================================================================
    
    def save_tournament(self, tournament_data: Dict, is_draft: bool = True) -> str:
        """
        Save complete tournament (event with all matches and stats).
        
        Args:
            tournament_data: Complete tournament data structure
            is_draft: If True, saves as draft; if False, publishes
        
        Returns:
            Event UUID
        """
        # Extract tournament info
        series_name = tournament_data.get('series_name', 'Series 1')
        year = tournament_data.get('year', datetime.now().year)
        event_number = tournament_data.get('event_number', 1)
        event_date = tournament_data.get('event_date')
        
        # Get or create series
        series_id = self.get_or_create_series(series_name, year)
        
        # Check if event exists
        existing_event = self.supabase.table('events')\
            .select('id, version_number')\
            .eq('series_id', series_id)\
            .eq('event_number', event_number)\
            .execute()
        
        if existing_event.data:
            # Update existing event
            event_id = existing_event.data[0]['id']
            current_version = existing_event.data[0]['version_number']
            
            event_payload = {
                'event_date': event_date,
                'status': 'published' if not is_draft else 'draft',
                'version_number': current_version + 1 if not is_draft else current_version
            }
            
            self.supabase.table('events')\
                .update(event_payload)\
                .eq('id', event_id)\
                .execute()
            
            # Delete existing matches for this event
            self.supabase.table('matches').delete().eq('event_id', event_id).execute()
        else:
            # Create new event
            event_payload = {
                'series_id': series_id,
                'event_number': event_number,
                'event_date': event_date,
                'status': 'published' if not is_draft else 'draft',
                'version_number': 1 if not is_draft else 0
            }
            
            result = self.supabase.table('events').insert(event_payload).execute()
            event_id = result.data[0]['id']
        
        # Process players and matches
        players_map = {}  # Map local player names to UUIDs
        
        for player_data in tournament_data.get('players', []):
            player_id = self.get_or_create_player(player_data)
            players_map[player_data['name']] = player_id
        
        # Save matches
        for match_data in tournament_data.get('matches', []):
            self._save_match(event_id, match_data, players_map)
        
        # Update personal bests if published
        if not is_draft:
            self._update_personal_bests_for_event(event_id, tournament_data)
            self.increment_version()
        
        # Save edit history
        if existing_event.data:
            self.save_edit_history(event_id, {
                'action': 'updated',
                'is_draft': is_draft,
                'timestamp': datetime.now().isoformat()
            })
        
        return event_id
    
    def _save_match(self, event_id: str, match_data: Dict, players_map: Dict):
        """
        Save a single match with stats.
        
        Args:
            event_id: UUID of event
            match_data: Match data dictionary
            players_map: Mapping of player names to UUIDs
        """
        player1_name = match_data.get('player1_name')
        player2_name = match_data.get('player2_name')
        
        if not player1_name or not player2_name:
            return
        
        player1_id = players_map.get(player1_name)
        player2_id = players_map.get(player2_name)
        
        if not player1_id or not player2_id:
            return
        
        # Insert match
        match_payload = {
            'event_id': event_id,
            'round_type': match_data.get('round_type', 'round_robin'),
            'round_number': match_data.get('round_number'),
            'group_name': match_data.get('group'),
            'player1_id': player1_id,
            'player2_id': player2_id,
            'player1_sets': match_data.get('player1_sets', 0),
            'player2_sets': match_data.get('player2_sets', 0),
            'player1_legs': match_data.get('player1_legs', 0),
            'player2_legs': match_data.get('player2_legs', 0)
        }
        
        match_result = self.supabase.table('matches').insert(match_payload).execute()
        match_id = match_result.data[0]['id']
        
        # Insert stats for both players
        for player_key in ['player1', 'player2']:
            player_name = match_data.get(f'{player_key}_name')
            player_id = players_map.get(player_name)
            stats = match_data.get(f'{player_key}_stats', {})
            
            if not stats or not player_id:
                continue
            
            # Calculate checkout percentage
            checkouts_hit = stats.get('checkouts_hit', 0)
            checkouts_opp = stats.get('checkouts_opportunities', 0)
            checkout_pct = (checkouts_hit / checkouts_opp * 100) if checkouts_opp > 0 else 0
            
            # Calculate legs lost
            legs_won = stats.get('legs_won', 0)
            total_legs = match_data.get('player1_legs', 0) + match_data.get('player2_legs', 0)
            legs_lost = total_legs - legs_won
            
            stats_payload = {
                'match_id': match_id,
                'player_id': player_id,
                'legs_won': legs_won,
                'legs_lost': legs_lost,
                'three_dart_avg': stats.get('three_dart_avg'),
                'count_100plus': stats.get('count_100plus', 0),
                'count_120plus': stats.get('count_120plus', 0),
                'count_140plus': stats.get('count_140plus', 0),
                'count_160plus': stats.get('count_160plus', 0),
                'count_180s': stats.get('count_180s', 0),
                'checkouts_hit': checkouts_hit,
                'checkouts_opportunities': checkouts_opp,
                'checkout_percentage': round(checkout_pct, 2),
                'highest_finish': stats.get('highest_finish', 0)
            }
            
            self.supabase.table('match_stats').insert(stats_payload).execute()
    
    def load_tournament(self, event_id: str) -> Optional[Dict]:
        """
        Load complete tournament data for editing.
        
        Args:
            event_id: UUID of event
        
        Returns:
            Complete tournament data structure
        """
        # Get event with series
        event_result = self.supabase.table('events')\
            .select('*, series(*)')\
            .eq('id', event_id)\
            .execute()
        
        if not event_result.data:
            return None
        
        event = event_result.data[0]
        
        # Get matches with stats
        matches_result = self.supabase.table('matches')\
            .select('*, match_stats(*)')\
            .eq('event_id', event_id)\
            .execute()
        
        # Get player info
        player_ids = set()
        for match in matches_result.data:
            player_ids.add(match['player1_id'])
            player_ids.add(match['player2_id'])
        
        players = {}
        for player_id in player_ids:
            player = self.get_player(player_id)
            if player:
                players[player_id] = player
        
        # Build tournament structure
        tournament = {
            'event_id': event_id,
            'series_name': event['series']['name'],
            'series_id': event['series_id'],
            'year': event['series']['year'],
            'event_number': event['event_number'],
            'event_date': event['event_date'],
            'status': event['status'],
            'version_number': event['version_number'],
            'players': list(players.values()),
            'matches': []
        }
        
        # Format matches
        for match in matches_result.data:
            player1 = players.get(match['player1_id'])
            player2 = players.get(match['player2_id'])
            
            if not player1 or not player2:
                continue
            
            # Find stats for each player
            player1_stats = next((s for s in match['match_stats'] if s['player_id'] == match['player1_id']), {})
            player2_stats = next((s for s in match['match_stats'] if s['player_id'] == match['player2_id']), {})
            
            match_data = {
                'match_id': match['id'],
                'round_type': match['round_type'],
                'round_number': match['round_number'],
                'group': match['group_name'],
                'player1_name': player1['name'],
                'player2_name': player2['name'],
                'player1_sets': match['player1_sets'],
                'player2_sets': match['player2_sets'],
                'player1_legs': match['player1_legs'],
                'player2_legs': match['player2_legs'],
                'player1_stats': player1_stats,
                'player2_stats': player2_stats
            }
            
            tournament['matches'].append(match_data)
        
        return tournament
    
    def get_all_events(self, status: Optional[str] = None) -> List[Dict]:
        """
        Get all events, optionally filtered by status.
        
        Args:
            status: 'draft', 'published', or None for all
        
        Returns:
            List of events with series info
        """
        query = self.supabase.table('events').select('*, series(*)')
        
        if status:
            query = query.eq('status', status)
        
        result = query.order('series_id', desc=False)\
                     .order('event_number', desc=False)\
                     .execute()
        
        return result.data
    
    def delete_event(self, event_id: str):
        """
        Delete an event (cascades to matches and stats).
        
        Args:
            event_id: UUID of event
        """
        self.supabase.table('events').delete().eq('id', event_id).execute()
    
    # ========================================================================
    # STATISTICS AND LEADERBOARDS
    # ========================================================================
    
    def get_event_leaderboard(self, event_id: str) -> List[Dict]:
        """
        Get leaderboard for specific event.
        
        Args:
            event_id: UUID of event
        
        Returns:
            List of player stats for event, sorted by legs won percentage
        """
        result = self.supabase.table('event_leaderboards')\
            .select('*')\
            .eq('event_id', event_id)\
            .order('legs_won', desc=True)\
            .execute()
        
        return result.data
    
    def get_all_time_standings(self) -> List[Dict]:
        """
        Get all-time standings ranked by legs won percentage.
        
        Returns:
            List of player career stats sorted by legs won %
        """
        result = self.supabase.table('player_career_stats')\
            .select('*')\
            .order('legs_won_percentage', desc=True)\
            .execute()
        
        return result.data
    
    def calculate_career_stats(self, player_id: str) -> Dict:
        """
        Calculate comprehensive career statistics for a player.
        
        Args:
            player_id: UUID of player
        
        Returns:
            Dictionary of career statistics
        """
        # This uses the player_career_stats view
        result = self.supabase.table('player_career_stats')\
            .select('*')\
            .eq('player_id', player_id)\
            .execute()
        
        if result.data:
            return result.data[0]
        
        return {}
    
    # ========================================================================
    # PERSONAL BESTS
    # ========================================================================
    
    def _update_personal_bests_for_event(self, event_id: str, tournament_data: Dict):
        """
        Update personal bests based on event placements.
        
        Args:
            event_id: UUID of event
            tournament_data: Tournament data with placements
        """
        placements = tournament_data.get('placements', {})
        
        for player_name, placement in placements.items():
            player_id = self.smart_match_player(player_name)
            if not player_id:
                continue
            
            # Check current personal best
            current = self.supabase.table('player_personal_bests')\
                .select('best_placement')\
                .eq('player_id', player_id)\
                .execute()
            
            if current.data:
                current_best = current.data[0]['best_placement']
                if placement < current_best:
                    # Update to better placement
                    self.supabase.table('player_personal_bests')\
                        .update({'best_placement': placement, 'best_event_id': event_id})\
                        .eq('player_id', player_id)\
                        .execute()
            else:
                # Insert new personal best
                self.supabase.table('player_personal_bests')\
                    .insert({
                        'player_id': player_id,
                        'best_placement': placement,
                        'best_event_id': event_id
                    })\
                    .execute()
    
    def get_player_personal_best(self, player_id: str) -> Optional[Dict]:
        """
        Get player's personal best placement.
        
        Args:
            player_id: UUID of player
        
        Returns:
            Personal best info or None
        """
        result = self.supabase.table('player_personal_bests')\
            .select('*, events(*, series(*))')\
            .eq('player_id', player_id)\
            .execute()
        
        if result.data:
            return result.data[0]
        return None
    
    # ========================================================================
    # EDIT HISTORY
    # ========================================================================
    
    def save_edit_history(self, event_id: str, changes: Dict, admin_note: str = None):
        """
        Save edit history for audit trail.
        
        Args:
            event_id: UUID of event
            changes: Dictionary of changes made
            admin_note: Optional note about the edit
        """
        payload = {
            'event_id': event_id,
            'changes_json': changes,
            'admin_note': admin_note
        }
        
        self.supabase.table('edit_history').insert(payload).execute()
    
    def get_edit_history(self, event_id: str) -> List[Dict]:
        """
        Get edit history for an event.
        
        Args:
            event_id: UUID of event
        
        Returns:
            List of edit history entries
        """
        result = self.supabase.table('edit_history')\
            .select('*')\
            .eq('event_id', event_id)\
            .order('timestamp', desc=True)\
            .execute()
        
        return result.data
    
    # ========================================================================
    # VERSION MANAGEMENT (for auto-refresh)
    # ========================================================================
    
    def get_current_version(self) -> int:
        """
        Get current published version number.
        
        Returns:
            Version number
        """
        result = self.supabase.table('app_version')\
            .select('version_number')\
            .eq('id', 1)\
            .execute()
        
        if result.data:
            return result.data[0]['version_number']
        return 0
    
    def increment_version(self):
        """Increment version number (called on publish)."""
        current = self.get_current_version()
        
        self.supabase.table('app_version')\
            .update({
                'version_number': current + 1,
                'last_published_at': datetime.now().isoformat()
            })\
            .eq('id', 1)\
            .execute()
    
    # ========================================================================
    # DATA EXPORT/BACKUP
    # ========================================================================
    
    def export_all_data(self) -> Dict:
        """
        Export complete database as JSON for backup.
        
        Returns:
            Complete database structure
        """
        return {
            'players': self.get_all_players(),
            'series': self.get_all_series(),
            'events': self.get_all_events(),
            'exported_at': datetime.now().isoformat()
        }
    
    def import_data(self, data: Dict):
        """
        Import data from backup (for restore functionality).
        
        Args:
            data: Complete database structure
        """
        # This would require careful implementation to avoid duplicates
        # For now, this is a placeholder
        pass


# Example usage
if __name__ == "__main__":
    manager = AADSDataManager()
    
    # Test connection
    version = manager.get_current_version()
    print(f"Current version: {version}")
    
    # Get all players
    players = manager.get_all_players()
    print(f"Total players: {len(players)}")
