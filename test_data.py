"""
Test script to populate the AADS database with sample data
"""

from database_manager import AADSDataManager

# Initialize the database manager
manager = AADSDataManager()

# Sample players and their statistics for Event 1
event_1_players = [
    {
        "name": "Michael Smith",
        "stats": {
            "three_dart_avg": 85.3,
            "legs_played": 8,
            "first_9_avg": 88.5,
            "hundreds_plus": 18,
            "one_forty_plus": 7,
            "one_eighties": 3,
            "high_finish": 141
        }
    },
    {
        "name": "Peter Wright",
        "stats": {
            "three_dart_avg": 82.7,
            "legs_played": 7,
            "first_9_avg": 85.2,
            "hundreds_plus": 15,
            "one_forty_plus": 5,
            "one_eighties": 2,
            "high_finish": 132
        }
    },
    {
        "name": "Gary Anderson",
        "stats": {
            "three_dart_avg": 79.4,
            "legs_played": 6,
            "first_9_avg": 82.1,
            "hundreds_plus": 12,
            "one_forty_plus": 4,
            "one_eighties": 1,
            "high_finish": 124
        }
    },
    {
        "name": "Rob Cross",
        "stats": {
            "three_dart_avg": 77.8,
            "legs_played": 5,
            "first_9_avg": 80.0,
            "hundreds_plus": 10,
            "one_forty_plus": 3,
            "one_eighties": 1,
            "high_finish": 100
        }
    },
    {
        "name": "Dave Chisnall",
        "stats": {
            "three_dart_avg": 76.2,
            "legs_played": 5,
            "first_9_avg": 78.5,
            "hundreds_plus": 9,
            "one_forty_plus": 2,
            "one_eighties": 0,
            "high_finish": 96
        }
    }
]

# Add Event 1 players
print("Adding Event 1 players...")
for player in event_1_players:
    manager.add_match_stats(player["name"], 1, player["stats"])
    print(f"  ✓ Added {player['name']}")

# Set Event 1 winner (Michael Smith)
manager.set_event_winner(1, "Michael Smith")
print("\n✓ Set Michael Smith as Event 1 winner (Qualified for Tournament of Champions)")

# Add some Event 2 players (some returning, some new)
print("\nAdding Event 2 players...")

event_2_players = [
    {
        "name": "Peter Wright",  # Returning player
        "stats": {
            "three_dart_avg": 84.1,
            "legs_played": 7,
            "first_9_avg": 86.3,
            "hundreds_plus": 16,
            "one_forty_plus": 6,
            "one_eighties": 2,
            "high_finish": 138
        }
    },
    {
        "name": "Nathan Aspinall",  # New player
        "stats": {
            "three_dart_avg": 81.5,
            "legs_played": 6,
            "first_9_avg": 83.7,
            "hundreds_plus": 14,
            "one_forty_plus": 5,
            "one_eighties": 2,
            "high_finish": 120
        }
    },
    {
        "name": "Jonny Clayton",  # New player
        "stats": {
            "three_dart_avg": 78.9,
            "legs_played": 5,
            "first_9_avg": 81.2,
            "hundreds_plus": 11,
            "one_forty_plus": 3,
            "one_eighties": 1,
            "high_finish": 110
        }
    }
]

for player in event_2_players:
    manager.add_match_stats(player["name"], 2, player["stats"])
    print(f"  ✓ Added {player['name']}")

# Set Event 2 winner (Peter Wright)
manager.set_event_winner(2, "Peter Wright")
print("\n✓ Set Peter Wright as Event 2 winner (Qualified for Tournament of Champions)")

# Display final leaderboard
print("\n" + "="*60)
print("AADS CHAMPIONSHIP STANDINGS")
print("="*60)

leaderboard = manager.get_leaderboard()
print(f"\n{'Rank':<6} {'Player':<20} {'Events':<8} {'3DA':<8} {'180s':<6} {'Status'}")
print("-" * 60)

for player in leaderboard:
    status = "✓ QUALIFIED" if player['qualified'] else "Competing"
    print(f"{player['rank']:<6} {player['name']:<20} {len(player['events_played']):<8} "
          f"{player['weighted_3da']:<8.2f} {player['total_180s']:<6} {status}")

print("\n" + "="*60)
print(f"Total Players: {len(leaderboard)}")
print(f"Qualified: {len([p for p in leaderboard if p['qualified']])}")
print("="*60)

print("\n✅ Test data loaded successfully!")
print("🌐 View the dashboard at: http://localhost:5000")
