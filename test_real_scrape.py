"""
Test the updated scraper with the real DartConnect URL
"""
from scraper import DartConnectScraper
import json

# Initialize scraper
scraper = DartConnectScraper()

# Test URL from Atlantic Amateur Darts Series
test_url = "https://recap.dartconnect.com/matches/688e209bf4fc02e124e72676"

print(f"Testing scraper with URL: {test_url}")
print("=" * 70)

try:
    # Attempt to scrape
    players = scraper.scrape_match_recap(test_url)
    
    print(f"\nScrape Result:")
    print(f"  Players found: {len(players)}")
    
    if players:
        print("\n" + "=" * 70)
        print("PLAYER STATISTICS:")
        print("=" * 70)
        
        for player in players:
            print(f"\nPlayer: {player['player_name']}")
            print(f"  3-Dart Average: {player['three_dart_avg']:.2f}")
            print(f"  Legs Played: {player['legs_played']}")
            print(f"  180s: {player['one_eighties']}")
            print(f"  140+: {player['one_forty_plus']}")
            print(f"  100+: {player['hundreds_plus']}")
            print(f"  High Finish: {player['high_finish']}")
    
        # Save full result to file for inspection
        with open('scrape_result.json', 'w') as f:
            json.dump(players, f, indent=2)
        print("\n" + "=" * 70)
        print("✅ Results saved to scrape_result.json")
    else:
        print("\n❌ No players found - page may be unavailable or format may have changed")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
