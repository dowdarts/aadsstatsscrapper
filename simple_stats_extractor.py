#!/usr/bin/env python3
"""
SIMPLE Event Stats Extractor
Uses the already-scraped Event #1 data and displays it in simple format

This script:
1. Loads the successfully scraped Event #1 data 
2. Aggregates player statistics
3. Displays results in clean format
4. Optionally integrates with backend database
"""

import json
from datetime import datetime
from typing import Dict, List


def load_scraped_event1_data() -> Dict:
    """Load the Event #1 data that was successfully scraped"""
    try:
        with open('event1_scraped_data_20251219_070828.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Event #1 data file not found")
        return None


def aggregate_player_stats(scraped_data: Dict) -> Dict:
    """
    Aggregate player statistics from all matches
    
    Args:
        scraped_data: The scraped JSON data
        
    Returns:
        Dictionary with aggregated player stats
    """
    players = {}
    
    print(f"📊 Processing {len(scraped_data['matches'])} matches...")
    
    for match in scraped_data['matches']:
        for player_data in match['players']:
            name = player_data['name']
            
            if name not in players:
                players[name] = {
                    'name': name,
                    'total_matches': 0,
                    'total_legs': 0,
                    'total_wins': 0,
                    'total_points': 0,
                    'total_darts': 0,
                    'total_180s': 0,
                    'highest_checkout': 0,
                    'best_first_9': 0,
                    'matches': []
                }
            
            p = players[name]
            p['total_matches'] += 1
            p['total_legs'] += player_data.get('leg_wins', 0)
            p['total_wins'] += player_data.get('set_wins', 0)
            
            # Parse points and darts
            points_str = str(player_data.get('points_scored_ppr', '0')).replace(',', '')
            darts_str = str(player_data.get('darts_thrown_ppr', '0')).replace(',', '')
            
            try:
                points = int(points_str)
                darts = int(darts_str)
                p['total_points'] += points
                p['total_darts'] += darts
            except (ValueError, TypeError):
                print(f"  ⚠️ Invalid points/darts for {name}: {points_str}/{darts_str}")
            
            # 180s and other stats
            p['total_180s'] += player_data.get('180s', 0)
            
            # Track highest values
            if player_data.get('highest_checkout'):
                p['highest_checkout'] = max(p['highest_checkout'], player_data.get('highest_checkout', 0))
            
            if player_data.get('first_nine_average'):
                p['best_first_9'] = max(p['best_first_9'], player_data.get('first_nine_average', 0))
            
            # Store match details
            p['matches'].append({
                'match_id': match['match_id'],
                'legs': player_data.get('leg_wins', 0),
                'sets': player_data.get('set_wins', 0),
                'ppr': player_data.get('ppr', '0'),
                '180s': player_data.get('180s', 0),
                'checkout_pct': player_data.get('checkout_percentage', '0'),
                'first_9': player_data.get('first_nine_average', 0)
            })
    
    # Calculate overall averages
    for player_data in players.values():
        if player_data['total_darts'] > 0:
            player_data['overall_average'] = round(player_data['total_points'] / player_data['total_darts'] * 3, 2)
        else:
            player_data['overall_average'] = 0.0
            
        if player_data['total_legs'] > 0:
            player_data['win_percentage'] = round((player_data['total_wins'] / player_data['total_legs']) * 100, 1)
        else:
            player_data['win_percentage'] = 0.0
    
    return players


def display_results(players: Dict):
    """Display the aggregated results in a clean format"""
    print("\n" + "="*80)
    print("🎯 ATLANTIC AMATEUR DART SERIES EVENT #1 - FINAL STANDINGS")
    print("="*80)
    
    # Sort by overall average
    sorted_players = sorted(
        players.items(), 
        key=lambda x: x[1]['overall_average'], 
        reverse=True
    )
    
    print(f"\n🏆 TOP PERFORMERS (by Average):")
    print("-" * 80)
    print(f"{'Rank':<4} {'Player':<15} {'Avg':<8} {'Legs':<6} {'180s':<6} {'Matches':<8} {'Win %':<8}")
    print("-" * 80)
    
    for i, (name, stats) in enumerate(sorted_players, 1):
        print(f"{i:<4} {name:<15} {stats['overall_average']:<8.2f} {stats['total_legs']:<6} {stats['total_180s']:<6} {stats['total_matches']:<8} {stats['win_percentage']:<8.1f}%")
    
    print("\n" + "="*80)
    print("📈 DETAILED STATISTICS")
    print("="*80)
    
    for name, stats in sorted_players:
        print(f"\n👤 {name.upper()}")
        print(f"   Overall Average: {stats['overall_average']:.2f}")
        print(f"   Total Legs: {stats['total_legs']} (Won: {stats['total_wins']})")
        print(f"   Total 180s: {stats['total_180s']}")
        print(f"   Highest Checkout: {stats['highest_checkout']}")
        print(f"   Best First 9: {stats['best_first_9']:.2f}")
        print(f"   Matches Played: {stats['total_matches']}")
        print(f"   Win Percentage: {stats['win_percentage']:.1f}%")


def save_simple_results(players: Dict, filename: str = None):
    """Save results in simple JSON format"""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"event1_simple_results_{timestamp}.json"
    
    results = {
        'event_name': 'Atlantic Amateur Dart Series Event #1',
        'processed_at': datetime.now().isoformat(),
        'total_players': len(players),
        'players': players
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {filename}")
    return filename


def main():
    """Main function"""
    print("🎯 AADS Event #1 - Simple Stats Extractor")
    print("="*60)
    
    # Load the scraped data
    scraped_data = load_scraped_event1_data()
    if not scraped_data:
        print("❌ No data to process")
        return
    
    print(f"✅ Loaded data: {scraped_data['total_matches_found']} matches")
    
    # Aggregate player statistics
    players = aggregate_player_stats(scraped_data)
    
    if not players:
        print("❌ No player data found")
        return
    
    print(f"✅ Processed {len(players)} players")
    
    # Display results
    display_results(players)
    
    # Save results
    filename = save_simple_results(players)
    
    print(f"\n🎉 Complete! Event #1 statistics processed successfully.")
    print(f"📊 {len(players)} players analyzed from {scraped_data['total_matches_found']} matches")
    
    return players


if __name__ == "__main__":
    main()