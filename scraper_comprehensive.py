"""
Comprehensive DartConnect Scraper
Extracts ALL statistics from Player Performance and Match Counts tabs
Uses direct HTTP requests to DartConnect's /players/ and /counts/ endpoints
"""

import requests
from bs4 import BeautifulSoup
import json
import html
from typing import Dict, List, Optional


def scrape_match_comprehensive(match_id: str) -> Dict:
    """
    Scrape comprehensive statistics for a match from DartConnect's tab endpoints
    
    Args:
        match_id: DartConnect match ID (e.g., '688e09b7f4fc02e124e7187f')
        
    Returns:
        Dictionary with complete player statistics including:
        - Basic stats (legs, wins, average, darts, points)
        - First 9 average
        - High scores (180s, 140+, 100+)
        - Checkout statistics
        - Double out statistics
    """
    
    # Construct URLs for both tabs
    players_url = f"https://recap.dartconnect.com/players/{match_id}"
    counts_url = f"https://recap.dartconnect.com/counts/{match_id}"
    
    result = {
        'match_id': match_id,
        'players': [],
        'errors': []
    }
    
    try:
        # Fetch Player Performance tab
        print(f"Fetching Player Performance: {players_url}")
        response_players = requests.get(players_url, timeout=10)
        response_players.raise_for_status()
        
        soup_players = BeautifulSoup(response_players.text, 'html.parser')
        app_div_players = soup_players.find('div', {'id': 'app'})
        
        if not app_div_players or 'data-page' not in app_div_players.attrs:
            result['errors'].append("Could not find Inertia.js data in Player Performance tab")
            return result
        
        page_data_players = json.loads(html.unescape(app_div_players['data-page']))
        players_data = page_data_players.get('props', {}).get('players', [])
        
        # Fetch Match Counts tab
        print(f"Fetching Match Counts: {counts_url}")
        response_counts = requests.get(counts_url, timeout=10)
        response_counts.raise_for_status()
        
        soup_counts = BeautifulSoup(response_counts.text, 'html.parser')
        app_div_counts = soup_counts.find('div', {'id': 'app'})
        
        if not app_div_counts or 'data-page' not in app_div_counts.attrs:
            result['errors'].append("Could not find Inertia.js data in Match Counts tab")
            return result
        
        page_data_counts = json.loads(html.unescape(app_div_counts['data-page']))
        performances = page_data_counts.get('props', {}).get('playerPerformances', [])
        match_info = page_data_counts.get('props', {}).get('matchInfo', {})
        
        # Combine data from both tabs
        for i, player in enumerate(players_data):
            player_stats = {
                'name': player.get('name'),
                'total_games': player.get('total_games'),
                'total_wins': player.get('total_wins'),
                'win_percentage': player.get('win_percentage'),
                'points_scored': player.get('points_scored_01', '').replace(',', ''),
                'darts_thrown': player.get('darts_thrown_01'),
                'average': player.get('average_01'),
                'card_link': player.get('card_link'),
            }
            
            # Add advanced stats from Match Counts tab if available
            if i < len(performances):
                perf = performances[i]
                dist = perf.get('dist', {})
                plus_100 = dist.get('plus_100', {})
                do_stats = perf.get('double_out_stats', {})
                
                player_stats.update({
                    'first_nine_avg': perf.get('first_nine'),
                    'avg_finish': perf.get('avg_finish'),
                    
                    # High Scores
                    'count_180s': 0 if plus_100.get('180') == '-' else int(plus_100.get('180', 0)),
                    'count_140_plus': _calculate_140_plus(plus_100),
                    'count_100_plus': plus_100.get('count', 0),
                    'highest_score': plus_100.get('highest'),
                    
                    # Checkout Stats
                    'checkout_efficiency': perf.get('coe', '-'),
                    'checkout_opportunities': perf.get('coo', 0),
                    'checkouts_hit': perf.get('cod', 0),
                    'highest_checkout': do_stats.get('highest'),
                })
            
            result['players'].append(player_stats)
        
        # Add match metadata
        result['match_info'] = {
            'competition': match_info.get('competition_title'),
            'event': match_info.get('event_title'),
            'date': match_info.get('match_start_date'),
            'duration': match_info.get('match_length'),
            'total_legs': match_info.get('total_games'),
            'winner_index': match_info.get('match_winner')
        }
        
        print(f"✅ Successfully scraped {len(result['players'])} players")
        
    except requests.RequestException as e:
        result['errors'].append(f"Request error: {str(e)}")
    except json.JSONDecodeError as e:
        result['errors'].append(f"JSON parsing error: {str(e)}")
    except Exception as e:
        result['errors'].append(f"Unexpected error: {str(e)}")
    
    return result


def _calculate_140_plus(plus_100: Dict) -> int:
    """Calculate total 140+ scores from distribution data"""
    count = 0
    
    # 140-159 range
    val = plus_100.get('140_159', '-')
    if val != '-':
        count += int(val)
    
    # 160-179 range
    val = plus_100.get('160_179', '-')
    if val != '-':
        count += int(val)
    
    # 180s
    val = plus_100.get('180', '-')
    if val != '-':
        count += int(val)
    
    return count


def print_match_stats(match_data: Dict):
    """Pretty print match statistics"""
    
    print("\n" + "="*80)
    print("MATCH STATISTICS")
    print("="*80)
    
    if 'match_info' in match_data:
        info = match_data['match_info']
        print(f"\n📋 {info.get('competition')}")
        print(f"   {info.get('event')}")
        print(f"   Date: {info.get('date')}")
        print(f"   Duration: {info.get('duration')}")
        print(f"   Total Legs: {info.get('total_legs')}")
    
    if not match_data['players']:
        print("\n❌ No player data found")
        if match_data['errors']:
            print("\nErrors:")
            for error in match_data['errors']:
                print(f"  - {error}")
        return
    
    print(f"\n{'='*80}")
    print(f"PLAYER STATISTICS ({len(match_data['players'])} players)")
    print(f"{'='*80}")
    
    for i, player in enumerate(match_data['players']):
        is_winner = (i == match_data.get('match_info', {}).get('winner_index'))
        winner_mark = " 🏆" if is_winner else ""
        
        print(f"\n{'─'*80}")
        print(f"PLAYER {i+1}: {player['name']}{winner_mark}")
        print(f"{'─'*80}")
        
        print(f"\n📊 OVERALL:")
        print(f"   Legs: {player['total_wins']}/{player['total_games']} ({player['win_percentage']}%)")
        print(f"   Points: {player['points_scored']} in {player['darts_thrown']} darts")
        print(f"   ⭐ Average: {player['average']}")
        
        if 'first_nine_avg' in player:
            print(f"\n🎯 ADVANCED:")
            print(f"   First 9 Average: {player['first_nine_avg']}")
            
            print(f"\n🔥 HIGH SCORES:")
            print(f"   180s: {player['count_180s']}")
            print(f"   140+: {player['count_140_plus']}")
            print(f"   100+: {player['count_100_plus']}")
            print(f"   Highest: {player['highest_score']}")
            
            print(f"\n🎪 CHECKOUTS:")
            print(f"   Efficiency: {player['checkout_efficiency']}")
            print(f"   Hit: {player['checkouts_hit']}/{player['checkout_opportunities']}")
            print(f"   Highest: {player['highest_checkout']}")
            print(f"   Average Finish: {player['avg_finish']}")
        
        if player.get('card_link'):
            print(f"\n🔗 {player['card_link']}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    # Test with Match 2 from Event 1
    match_id = "688e09b7f4fc02e124e7187f"
    
    print("="*80)
    print("COMPREHENSIVE DARTCONNECT SCRAPER")
    print("="*80)
    print(f"\nMatch ID: {match_id}")
    
    # Scrape data
    match_data = scrape_match_comprehensive(match_id)
    
    # Print results
    print_match_stats(match_data)
    
    # Verification
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    print("\nExpected Results (Match 2, Event 1):")
    print("  ✓ Miguel Velasquez: 54.55 average, 2 wins")
    print("  ✓ Steve Rushton: 54.60 average, 3 wins")
    
    if match_data['players']:
        print("\nActual Results:")
        for player in match_data['players']:
            print(f"  {'✓' if player['average'] in ['54.55', '54.60'] else '✗'} {player['name']}: {player['average']} average, {player['total_wins']} wins")
