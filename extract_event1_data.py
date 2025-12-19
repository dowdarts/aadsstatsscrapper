#!/usr/bin/env python3
"""
Extract Event #1 Data and Save to Backend
Direct script to scrape Event #1 and save to aads_master_db.json for display
"""

from scraper_html_parser import scrape_event_comprehensive
from database_manager import AADSDataManager
import json
from datetime import datetime

def main():
    print("🎯 AADS Event #1 Data Extraction")
    print("=" * 50)
    
    # Event #1 URL
    event_url = "https://tv.dartconnect.com/event/mt_joe6163l_1"
    
    print(f"📊 Scraping Event #1: {event_url}")
    
    # Step 1: Scrape the event data
    results = scrape_event_comprehensive(event_url)
    
    if not results:
        print("❌ Failed to scrape event data")
        return False
    
    print(f"\n✅ Successfully scraped {results['successfully_scraped']} matches!")
    
    # Step 2: Initialize database manager
    db = AADSDataManager()
    
    # Step 3: Process each match and add to database
    print(f"\n📝 Processing matches for backend storage...")
    
    for i, match in enumerate(results['matches'], 1):
        print(f"  Processing match {i}: {match['players'][0]['name']} vs {match['players'][1]['name']}")
        
        # Convert match data to database format
        for player in match['players']:
            player_stats = {
                'player_name': player['name'],
                'match_id': match['match_id'],
                'points_scored': int(player['points_scored_ppr'].replace(',', '')) if player['points_scored_ppr'] else 0,
                'darts_thrown': int(player['darts_thrown_ppr']) if player['darts_thrown_ppr'] else 0,
                'dart_average': float(player['ppr']) if player['ppr'] else 0,
                'leg_wins': player['leg_wins'],
                'set_wins': player['set_wins'],
                'win_percentage': player['win_percentage'],
                '180s': player.get('180s', 0),
                'checkout_percentage': float(player.get('checkout_percentage', 0)) if player.get('checkout_percentage') else 0,
                'highest_checkout': player.get('highest_checkout', 0),
                'first_nine_average': player.get('first_nine_average', 0),
                'event_name': 'Event #1',
                'match_date': match['match_date'],
                'competition': match['competition_title']
            }
            
            # Add stats to database
            try:
                db.add_match_stats(
                    player_stats['player_name'],
                    player_stats['points_scored'],
                    player_stats['darts_thrown'],
                    player_stats['event_name'],
                    player_stats['match_id']
                )
                
                # Add advanced stats
                if player_stats['180s'] > 0:
                    for _ in range(player_stats['180s']):
                        db.add_180(player_stats['player_name'], player_stats['event_name'])
                
            except Exception as e:
                print(f"    ⚠️ Warning: Could not add stats for {player_stats['player_name']}: {e}")
    
    # Step 4: Save raw scraped data as backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"event1_scraped_data_{timestamp}.json"
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Raw data backed up to: {backup_file}")
    
    # Step 5: Display summary
    print(f"\n📊 FINAL SUMMARY:")
    print(f"🎯 Event: {event_url}")
    print(f"✅ Matches Scraped: {results['successfully_scraped']}")
    print(f"👥 Players Found:")
    
    all_players = set()
    for match in results['matches']:
        for player in match['players']:
            all_players.add(player['name'])
    
    for player in sorted(all_players):
        print(f"    • {player}")
    
    print(f"\n🎉 Event #1 data successfully extracted and saved to backend!")
    print(f"🌐 View the dashboard at: http://localhost:5000")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Mission accomplished! Event #1 data is ready for display.")
    else:
        print("\n❌ Mission failed. Please check the error messages above.")