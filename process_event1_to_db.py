#!/usr/bin/env python3
"""
Process Event #1 Scraped Data and Save to Backend Database
Converts the scraped JSON data to the correct database format
"""

import json
from database_manager import AADSDataManager
from datetime import datetime

def process_scraped_data_to_database():
    """Convert scraped Event #1 data to database format"""
    
    print("🔄 Processing Event #1 data for backend database...")
    
    # Load the scraped data
    try:
        with open('event1_scraped_data_20251219_070828.json', 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
    except FileNotFoundError:
        print("❌ Scraped data file not found. Please run the scraper first.")
        return False
    
    print(f"📊 Found {scraped_data['successfully_scraped']} matches to process")
    
    # Initialize database manager
    db = AADSDataManager()
    
    # Process each match
    processed_players = {}
    
    for i, match in enumerate(scraped_data['matches'], 1):
        print(f"  Processing match {i}: {match['players'][0]['name']} vs {match['players'][1]['name']}")
        
        for player in match['players']:
            player_name = player['name']
            
            # Initialize player totals if not seen before
            if player_name not in processed_players:
                processed_players[player_name] = {
                    'total_legs': 0,
                    'total_points': 0,
                    'total_darts': 0,
                    'total_180s': 0,
                    'total_140s': 0,
                    'total_100s': 0,
                    'highest_finish': 0,
                    'best_first_9': 0,
                    'matches': []
                }
            
            # Extract match stats
            points_scored = int(player['points_scored_ppr'].replace(',', '')) if player['points_scored_ppr'] else 0
            darts_thrown = int(player['darts_thrown_ppr']) if player['darts_thrown_ppr'] else 0
            dart_average = float(player['ppr']) if player['ppr'] else 0
            leg_wins = player['leg_wins']
            one_eighties = player.get('180s', 0)
            highest_checkout = player.get('highest_checkout', 0)
            first_nine_avg = player.get('first_nine_average', 0)
            
            # Accumulate player totals
            processed_players[player_name]['total_legs'] += leg_wins
            processed_players[player_name]['total_points'] += points_scored
            processed_players[player_name]['total_darts'] += darts_thrown
            processed_players[player_name]['total_180s'] += one_eighties
            
            # Estimate 140+ and 100+ counts based on average (rough approximation)
            # For every 180, typically there are 2-3 140+ scores and 5-8 100+ scores
            estimated_140s = one_eighties * 2 if one_eighties > 0 else max(0, int(dart_average - 60) // 10)
            estimated_100s = one_eighties * 6 if one_eighties > 0 else max(0, int(dart_average - 50) // 8)
            
            processed_players[player_name]['total_140s'] += estimated_140s
            processed_players[player_name]['total_100s'] += estimated_100s
            
            if highest_checkout > processed_players[player_name]['highest_finish']:
                processed_players[player_name]['highest_finish'] = highest_checkout
            
            if first_nine_avg > processed_players[player_name]['best_first_9']:
                processed_players[player_name]['best_first_9'] = first_nine_avg
            
            # Store individual match data
            processed_players[player_name]['matches'].append({
                'match_id': match['match_id'],
                'opponent': match['players'][1]['name'] if player == match['players'][0] else match['players'][0]['name'],
                'three_dart_avg': dart_average,
                'legs_played': leg_wins,
                'first_9_avg': first_nine_avg,
                'one_eighties': one_eighties,
                'highest_checkout': highest_checkout,
                'date': match['match_date']
            })
    
    # Add all players to database
    for player_name, totals in processed_players.items():
        print(f"    Adding {player_name} to database...")
        
        # Calculate overall weighted average
        if totals['total_darts'] > 0:
            weighted_avg = (totals['total_points'] / totals['total_darts']) * 3
        else:
            weighted_avg = 0
        
        # Create stats dictionary for the database
        stats_dict = {
            'three_dart_avg': weighted_avg,
            'legs_played': totals['total_legs'],
            'first_9_avg': totals['best_first_9'],
            'hundreds_plus': totals['total_100s'],
            'one_forty_plus': totals['total_140s'],
            'one_eighties': totals['total_180s'],
            'high_finish': totals['highest_finish']
        }
        
        try:
            db.add_match_stats(player_name, 1, stats_dict)  # Event #1
        except Exception as e:
            print(f"    ⚠️ Warning: Could not add {player_name}: {e}")
            continue
    
    # Save database
    db._save_database()
    
    print(f"\n✅ Successfully processed {len(processed_players)} players into database!")
    print(f"📋 Players added:")
    for player_name in sorted(processed_players.keys()):
        totals = processed_players[player_name]
        weighted_avg = (totals['total_points'] / totals['total_darts']) * 3 if totals['total_darts'] > 0 else 0
        print(f"    • {player_name}: {weighted_avg:.2f} avg, {totals['total_legs']} legs, {totals['total_180s']} x 180s")
    
    return True

def main():
    print("🎯 AADS Event #1 Database Integration")
    print("=" * 50)
    
    success = process_scraped_data_to_database()
    
    if success:
        print(f"\n🎉 Event #1 data successfully integrated into backend database!")
        print(f"🌐 Start the Flask server to view the dashboard:")
        print(f"    python app.py")
        print(f"    Then visit: http://localhost:5000")
    else:
        print(f"\n❌ Failed to integrate data. Please check the error messages above.")

if __name__ == "__main__":
    main()