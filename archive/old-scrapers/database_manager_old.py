"""
AADS Database Manager
Handles player statistics tracking across multiple events with weighted averages
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class AADSDataManager:
    """
    Manages the AADS Master Database for player statistics tracking.
    
    Key Features:
    - Weighted average calculation for 3DA across all legs
    - Event-specific history tracking
    - Qualification status for Tournament of Champions
    - Persistent JSON storage
    """
    
    def __init__(self, db_path: str = "aads_master_db.json"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the JSON database file
        """
        self.db_path = db_path
        self.data = self._load_database()
    
    def _load_database(self) -> Dict:
        """
        Load the database from JSON file or create a new one.
        
        Returns:
            Dictionary containing the database structure
        """
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Corrupted database file. Creating new database.")
                return self._create_empty_database()
        else:
            return self._create_empty_database()
    
    def _create_empty_database(self) -> Dict:
        """
        Create an empty database structure.
        
        Returns:
            Empty database dictionary
        """
        return {
            "series_info": {
                "name": "Atlantic Amateur Darts Series",
                "total_events": 7,
                "qualifying_events": 6,
                "championship_event": 7
            },
            "players": {},
            "events": {},
            "last_updated": None
        }
    
    def _save_database(self):
        """Save the current database state to JSON file."""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def add_match_stats(self, player_name: str, event_id: int, stats_dict: Dict):
        """
        Add or update match statistics for a player.
        
        Args:
            player_name: Name of the player
            event_id: Event number (1-7)
            stats_dict: Dictionary containing match statistics
                Required keys:
                - three_dart_avg: 3-dart average for this match
                - legs_played: Number of legs in this match
                - first_9_avg: First 9 average
                - hundreds_plus: Count of 100+ scores
                - one_forty_plus: Count of 140+ scores
                - one_eighties: Count of 180s
                - high_finish: Highest checkout
        """
        player_name = player_name.strip()
        
        # Initialize player if new
        if player_name not in self.data["players"]:
            self.data["players"][player_name] = {
                "name": player_name,
                "events_played": [],
                "total_legs": 0,
                "weighted_3da": 0.0,
                "total_180s": 0,
                "total_140s": 0,
                "total_100s": 0,
                "highest_finish": 0,
                "best_first_9": 0.0,
                "qualified": False,
                "event_wins": [],
                "event_history": []
            }
        
        player = self.data["players"][player_name]
        
        # Extract stats from dictionary
        match_3da = float(stats_dict.get("three_dart_avg", 0))
        legs_played = int(stats_dict.get("legs_played", 0))
        first_9 = float(stats_dict.get("first_9_avg", 0))
        hundreds = int(stats_dict.get("hundreds_plus", 0))
        one_forties = int(stats_dict.get("one_forty_plus", 0))
        one_eighties = int(stats_dict.get("one_eighties", 0))
        high_finish = int(stats_dict.get("high_finish", 0))
        
        # Update weighted 3DA (sum of all leg averages / total legs)
        current_total_dart_sum = player["weighted_3da"] * player["total_legs"]
        new_dart_sum = match_3da * legs_played
        player["total_legs"] += legs_played
        
        if player["total_legs"] > 0:
            player["weighted_3da"] = round(
                (current_total_dart_sum + new_dart_sum) / player["total_legs"], 
                2
            )
        
        # Update cumulative stats
        player["total_180s"] += one_eighties
        player["total_140s"] += one_forties
        player["total_100s"] += hundreds
        player["highest_finish"] = max(player["highest_finish"], high_finish)
        player["best_first_9"] = max(player["best_first_9"], first_9)
        
        # Track event participation
        if event_id not in player["events_played"]:
            player["events_played"].append(event_id)
        
        # Add event history entry
        event_entry = {
            "event_id": event_id,
            "date": datetime.now().isoformat(),
            "three_dart_avg": match_3da,
            "legs_played": legs_played,
            "first_9_avg": first_9,
            "one_eighties": one_eighties,
            "one_forty_plus": one_forties,
            "hundreds_plus": hundreds,
            "high_finish": high_finish
        }
        player["event_history"].append(event_entry)
        
        # Update event tracking
        if str(event_id) not in self.data["events"]:
            self.data["events"][str(event_id)] = {
                "event_id": event_id,
                "participants": [],
                "winner": None,
                "completed": False
            }
        
        if player_name not in self.data["events"][str(event_id)]["participants"]:
            self.data["events"][str(event_id)]["participants"].append(player_name)
        
        self._save_database()
    
    def set_event_winner(self, event_id: int, player_name: str):
        """
        Mark a player as the winner of an event.
        
        For qualifying events (1-6), this grants qualification to Event 7.
        
        Args:
            event_id: Event number (1-7)
            player_name: Name of the winning player
        """
        player_name = player_name.strip()
        
        if player_name not in self.data["players"]:
            raise ValueError(f"Player '{player_name}' not found in database")
        
        # Update event winner
        if str(event_id) not in self.data["events"]:
            self.data["events"][str(event_id)] = {
                "event_id": event_id,
                "participants": [],
                "winner": None,
                "completed": False
            }
        
        self.data["events"][str(event_id)]["winner"] = player_name
        self.data["events"][str(event_id)]["completed"] = True
        
        # Update player qualification status
        player = self.data["players"][player_name]
        if event_id not in player["event_wins"]:
            player["event_wins"].append(event_id)
        
        # Grant qualification for Tournament of Champions (if qualifying event)
        if 1 <= event_id <= 6:
            player["qualified"] = True
        
        self._save_database()
    
    def get_leaderboard(self, sort_by: str = "weighted_3da") -> List[Dict]:
        """
        Get the current leaderboard sorted by specified metric.
        
        Args:
            sort_by: Metric to sort by (weighted_3da, total_180s, etc.)
        
        Returns:
            List of player dictionaries sorted by the specified metric
        """
        players = list(self.data["players"].values())
        
        # Sort in descending order
        players.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
        
        # Add rank
        for i, player in enumerate(players, 1):
            player["rank"] = i
        
        return players
    
    def get_player_stats(self, player_name: str) -> Optional[Dict]:
        """
        Get statistics for a specific player.
        
        Args:
            player_name: Name of the player
        
        Returns:
            Player statistics dictionary or None if not found
        """
        return self.data["players"].get(player_name.strip())
    
    def get_qualified_players(self) -> List[Dict]:
        """
        Get all players qualified for the Tournament of Champions.
        
        Returns:
            List of qualified player dictionaries
        """
        return [
            player for player in self.data["players"].values()
            if player["qualified"]
        ]
    
    def get_event_details(self, event_id: int) -> Optional[Dict]:
        """
        Get details for a specific event.
        
        Args:
            event_id: Event number (1-7)
        
        Returns:
            Event details dictionary or None if not found
        """
        return self.data["events"].get(str(event_id))
    
    def get_all_data(self) -> Dict:
        """
        Get the complete database.
        
        Returns:
            Complete database dictionary
        """
        return self.data
    
    def reset_database(self):
        """Reset the database to empty state."""
        self.data = self._create_empty_database()
        self._save_database()


# Example usage and testing
if __name__ == "__main__":
    # Initialize manager
    manager = AADSDataManager()
    
    # Example: Add stats for a player
    example_stats = {
        "three_dart_avg": 75.5,
        "legs_played": 5,
        "first_9_avg": 80.2,
        "hundreds_plus": 12,
        "one_forty_plus": 4,
        "one_eighties": 2,
        "high_finish": 120
    }
    
    manager.add_match_stats("John Doe", 1, example_stats)
    
    # Get leaderboard
    leaderboard = manager.get_leaderboard()
    print(json.dumps(leaderboard, indent=2))
