"""
Batch Scraper for Atlantic Amateur Darts Series

This script allows you to scrape multiple DartConnect match recap URLs
and import them into the AADS database for a specific event.

Usage:
    python batch_scrape_event.py

You'll be prompted to enter:
1. Event number (1-7)
2. Match URLs (one per line, empty line to finish)
"""

import sys
from scraper import DartConnectScraper
from database_manager import AADSDataManager

def batch_scrape_event():
    """
    Interactively scrape multiple matches for an event
    """
    print("=" * 70)
    print("AADS Batch Match Scraper")
    print("=" * 70)
    
    # Initialize
    scraper = DartConnectScraper()
    db = AADSDataManager()
    
    # Get event number
    while True:
        try:
            event_num = input("\nEnter event number (1-7): ").strip()
            event_num = int(event_num)
            if 1 <= event_num <= 7:
                break
            else:
                print("❌ Event number must be between 1 and 7")
        except ValueError:
            print("❌ Please enter a valid number")
    
    print(f"\n✅ Scraping for Event {event_num}")
    print("\nEnter match recap URLs (one per line)")
    print("Press Enter on an empty line when done")
    print("Example: https://recap.dartconnect.com/matches/688e00ccf4fc02e124e7131c")
    print("-" * 70)
    
    # Collect URLs
    urls = []
    while True:
        url = input().strip()
        if not url:
            break
        if 'recap.dartconnect.com/matches/' in url:
            urls.append(url)
            print(f"  ✓ Added ({len(urls)} total)")
        else:
            print(f"  ⚠ Skipped (not a valid recap URL)")
    
    if not urls:
        print("\n❌ No URLs provided. Exiting.")
        return
    
    print(f"\n{'=' * 70}")
    print(f"Starting batch scrape of {len(urls)} matches for Event {event_num}")
    print("=" * 70)
    
    # Scrape each URL
    successful = 0
    failed = 0
    skipped = 0
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Scraping: {url}")
        
        try:
            players = scraper.scrape_match_recap(url)
            
            if not players:
                print(f"  ⚠ No player data found")
                skipped += 1
                continue
            
            print(f"  ✓ Found {len(players)} players")
            
            # Add each player's stats to the database
            for player in players:
                player_name = player['player_name']
                three_dart_avg = player['three_dart_avg']
                legs_played = player['legs_played']
                one_eighties = player['one_eighties']
                high_finish = player['high_finish']
                
                # Add to database
                db.add_match_stats(
                    player_name=player_name,
                    event_id=event_num,
                    three_dart_avg=three_dart_avg,
                    legs_played=legs_played,
                    one_eighties=one_eighties,
                    high_finish=high_finish
                )
                
                print(f"    • {player_name}: {three_dart_avg:.2f} avg ({legs_played} legs)")
            
            successful += 1
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1
    
    # Summary
    print(f"\n{'=' * 70}")
    print("BATCH SCRAPE COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}")
    print(f"⚠  Skipped:    {skipped}")
    print(f"❌ Failed:     {failed}")
    print(f"📊 Total:      {len(urls)}")
    
    # Show updated leaderboard
    print(f"\n{'=' * 70}")
    print("UPDATED LEADERBOARD")
    print("=" * 70)
    
    leaderboard = db.get_leaderboard()
    
    print(f"\n{'Rank':<6} {'Player':<25} {'3DA':<8} {'Events':<8} {'180s':<6}")
    print("-" * 70)
    
    for i, player in enumerate(leaderboard[:10], 1):
        print(f"{i:<6} {player['name']:<25} {player['weighted_3da']:<8.2f} "
              f"{player['events_played']:<8} {player['one_eighties']:<6}")
    
    print("\n✅ Data saved to aads_master_db.json")
    print(f"🌐 View dashboard at: http://localhost:5000")

if __name__ == "__main__":
    try:
        batch_scrape_event()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(0)
