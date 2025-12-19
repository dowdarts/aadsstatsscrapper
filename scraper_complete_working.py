"""
WORKING COMPREHENSIVE DART SCRAPER
Two-stage process: Extract match URLs from event, then scrape each match for full stats

STAGE 1: Extract match URLs using DartConnect API2
STAGE 2: Scrape each match using direct endpoints for comprehensive stats

This version saves to local JSON file to avoid Supabase upload issues
"""

import requests
import json
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import time
from typing import Dict, List
from datetime import datetime


def extract_match_urls_from_event(event_url: str) -> List[str]:
    """
    STAGE 1: Extract all match URLs from a DartConnect event page
    Uses the API2 endpoint for reliable extraction
    
    Args:
        event_url: Full event URL (e.g., https://tv.dartconnect.com/event/mt_joe6163l_1)
        
    Returns:
        List of match recap URLs
    """
    print(f"\n🎯 STAGE 1: Extracting match URLs from event")
    print(f"Event URL: {event_url}")
    
    # Extract event ID from URL
    event_id_match = re.search(r'/event/([a-zA-Z0-9_]+)', event_url)
    if not event_id_match:
        raise ValueError("Could not extract event ID from URL")
    
    event_id = event_id_match.group(1)
    print(f"Event ID: {event_id}")
    
    # Call DartConnect API2
    api_url = f"https://tv.dartconnect.com/api2/event/{event_id}/matches"
    print(f"Calling API2: {api_url}")
    
    request_obj = Request(api_url, method='POST')
    request_obj.add_header('Content-Type', 'application/json')
    request_obj.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        with urlopen(request_obj, timeout=30) as response:
            result = json.loads(response.read().decode())
        
        print(f"✅ API2 response received")
        
        # Extract match URLs from payload
        match_urls = []
        payload = result.get('payload', {})
        
        for section_name, section_data in payload.items():
            print(f"Processing section: {section_name}")
            if isinstance(section_data, list):
                for match in section_data:
                    if isinstance(match, dict) and 'mi' in match:
                        match_id = match['mi']
                        match_url = f"https://recap.dartconnect.com/matches/{match_id}"
                        match_urls.append(match_url)
                        print(f"  Found match: {match_id}")
        
        print(f"\n✅ STAGE 1 COMPLETE: Found {len(match_urls)} matches")
        return match_urls
        
    except Exception as e:
        print(f"❌ API2 failed: {e}")
        raise


def scrape_single_match_comprehensive(match_id: str) -> Dict:
    """
    STAGE 2: Scrape comprehensive stats from a single match
    Uses both /players/ and /counts/ endpoints for complete data
    
    Args:
        match_id: DartConnect match ID
        
    Returns:
        Dictionary with all player stats
    """
    players_url = f"https://recap.dartconnect.com/players/{match_id}"
    counts_url = f"https://recap.dartconnect.com/counts/{match_id}"
    
    result = {
        'match_id': match_id,
        'players': [],
        'success': False,
        'errors': []
    }
    
    try:
        # Get Player Performance data
        print(f"  📊 Fetching player performance...")
        response_players = requests.get(players_url, timeout=10)
        response_players.raise_for_status()
        
        # Get Match Counts data  
        print(f"  📊 Fetching match counts...")
        response_counts = requests.get(counts_url, timeout=10)
        response_counts.raise_for_status()
        
        # Parse both responses
        from bs4 import BeautifulSoup
        
        # Parse players data
        soup_players = BeautifulSoup(response_players.text, 'html.parser')
        app_div_players = soup_players.find('div', {'id': 'app'})
        
        if not app_div_players or 'data-page' not in app_div_players.attrs:
            result['errors'].append("No player performance data found")
            return result
        
        # Extract Inertia.js data from players tab
        data_page_players = app_div_players['data-page']
        page_data_players = json.loads(data_page_players)
        props_players = page_data_players.get('props', {})
        
        # Parse counts data
        soup_counts = BeautifulSoup(response_counts.text, 'html.parser')
        app_div_counts = soup_counts.find('div', {'id': 'app'})
        
        counts_data = {}
        if app_div_counts and 'data-page' in app_div_counts.attrs:
            data_page_counts = app_div_counts['data-page']
            page_data_counts = json.loads(data_page_counts)
            props_counts = page_data_counts.get('props', {})
            
            # Extract counts for each player
            if 'page' in props_counts and 'players' in props_counts['page']:
                for player_data in props_counts['page']['players']:
                    player_name = player_data.get('player_name', '')
                    counts_data[player_name] = player_data
        
        # Process player data
        if 'page' in props_players and 'players' in props_players['page']:
            for player_data in props_players['page']['players']:
                player_name = player_data.get('player_name', '')
                
                # Get counts data for this player
                player_counts = counts_data.get(player_name, {})
                
                # Build comprehensive player record
                player_record = {
                    'name': player_name,
                    'total_games': player_data.get('total_games', 0),
                    'total_wins': player_data.get('total_wins', 0),
                    'win_percentage': player_data.get('win_percentage', 0),
                    'darts_thrown': player_data.get('darts_thrown', 0),
                    'points_scored': player_data.get('points_scored', 0),
                    'average': player_data.get('average', 0),
                    'first_nine_avg': player_data.get('first_nine_avg'),
                    'highest_score': player_data.get('highest_score'),
                    
                    # Counts data
                    'count_180s': player_counts.get('count_180s', 0),
                    'count_140_plus': player_counts.get('count_140_plus', 0),
                    'count_100_plus': player_counts.get('count_100_plus', 0),
                    
                    # Checkout data
                    'checkout_opportunities': player_counts.get('checkout_opportunities', 0),
                    'checkouts_hit': player_counts.get('checkouts_hit', 0),
                    'checkout_efficiency': player_counts.get('checkout_efficiency', '-'),
                    'highest_checkout': player_counts.get('highest_checkout'),
                    'avg_finish': player_counts.get('avg_finish'),
                    
                    # Additional data
                    'card_link': f"https://recap.dartconnect.com/players/{match_id}"
                }
                
                result['players'].append(player_record)
        
        result['success'] = len(result['players']) > 0
        
        if result['success']:
            print(f"  ✅ Scraped {len(result['players'])} players")
        else:
            print(f"  ❌ No players found")
            result['errors'].append("No players found in match data")
        
        return result
        
    except Exception as e:
        result['errors'].append(str(e))
        print(f"  ❌ Error: {e}")
        return result


def scrape_full_event_comprehensive(event_url: str, event_name: str = "AADS Event") -> Dict:
    """
    COMPLETE EVENT SCRAPER
    
    Combines both stages:
    1. Extract all match URLs from event
    2. Scrape comprehensive stats from each match
    3. Save everything to JSON file
    
    Args:
        event_url: DartConnect event URL
        event_name: Human-readable event name
        
    Returns:
        Complete results dictionary
    """
    print(f"\n🚀 STARTING COMPREHENSIVE EVENT SCRAPE")
    print(f"Event: {event_name}")
    print(f"URL: {event_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # STAGE 1: Get match URLs
    try:
        match_urls = extract_match_urls_from_event(event_url)
        if not match_urls:
            return {
                'success': False,
                'error': 'No matches found in event',
                'event_name': event_name
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to extract matches: {str(e)}',
            'event_name': event_name
        }
    
    # STAGE 2: Scrape each match
    print(f"\n🔍 STAGE 2: Scraping {len(match_urls)} matches")
    print("="*80)
    
    results = {
        'event_name': event_name,
        'event_url': event_url,
        'scraped_at': datetime.now().isoformat(),
        'total_matches': len(match_urls),
        'successful_matches': 0,
        'failed_matches': 0,
        'all_players': {},  # Aggregated player stats
        'match_details': [],  # Individual match results
        'errors': []
    }
    
    # Process each match
    for i, match_url in enumerate(match_urls, 1):
        match_id = match_url.split('/')[-1]
        print(f"\n🎯 Match {i}/{len(match_urls)}: {match_id}")
        
        # Scrape with retries
        MAX_RETRIES = 3
        match_result = None
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                match_result = scrape_single_match_comprehensive(match_id)
                
                if match_result['success']:
                    results['successful_matches'] += 1
                    results['match_details'].append(match_result)
                    
                    # Aggregate player stats
                    for player in match_result['players']:
                        player_name = player['name']
                        if player_name not in results['all_players']:
                            results['all_players'][player_name] = {
                                'name': player_name,
                                'total_matches': 0,
                                'total_legs': 0,
                                'total_wins': 0,
                                'total_darts': 0,
                                'total_points': 0,
                                'total_180s': 0,
                                'total_140_plus': 0,
                                'total_100_plus': 0,
                                'total_checkout_opportunities': 0,
                                'total_checkouts_hit': 0,
                                'highest_checkout': 0,
                                'match_details': []
                            }
                        
                        # Add to aggregates
                        p = results['all_players'][player_name]
                        p['total_matches'] += 1
                        p['total_legs'] += player.get('total_games', 0)
                        p['total_wins'] += player.get('total_wins', 0)
                        p['total_darts'] += player.get('darts_thrown', 0)
                        p['total_points'] += int(str(player.get('points_scored', 0)).replace(',', ''))
                        p['total_180s'] += player.get('count_180s', 0)
                        p['total_140_plus'] += player.get('count_140_plus', 0)
                        p['total_100_plus'] += player.get('count_100_plus', 0)
                        p['total_checkout_opportunities'] += player.get('checkout_opportunities', 0)
                        p['total_checkouts_hit'] += player.get('checkouts_hit', 0)
                        
                        if player.get('highest_checkout'):
                            p['highest_checkout'] = max(p['highest_checkout'], player.get('highest_checkout', 0))
                        
                        # Store match detail
                        p['match_details'].append({
                            'match_id': match_id,
                            'legs': player.get('total_games', 0),
                            'wins': player.get('total_wins', 0),
                            'average': player.get('average', 0),
                            'first_nine_avg': player.get('first_nine_avg'),
                            'count_180s': player.get('count_180s', 0),
                            'count_140_plus': player.get('count_140_plus', 0),
                            'count_100_plus': player.get('count_100_plus', 0)
                        })
                    
                    print(f"  ✅ Success - {len(match_result['players'])} players")
                    break
                else:
                    results['failed_matches'] += 1
                    results['errors'].extend(match_result['errors'])
                    print(f"  ❌ No data found")
                    break
                    
            except Exception as e:
                if attempt < MAX_RETRIES:
                    print(f"  ⚠️ Attempt {attempt} failed, retrying...")
                    time.sleep(2)
                else:
                    results['failed_matches'] += 1
                    results['errors'].append(f"Match {match_id}: {str(e)}")
                    print(f"  ❌ Failed after {MAX_RETRIES} attempts")
                    break
        
        # Delay between matches
        if i < len(match_urls):
            time.sleep(1.5)
    
    # Calculate final stats for each player
    for player_name, player_data in results['all_players'].items():
        if player_data['total_darts'] > 0:
            player_data['overall_average'] = round(player_data['total_points'] / player_data['total_darts'] * 3, 2)
        else:
            player_data['overall_average'] = 0
            
        if player_data['total_legs'] > 0:
            player_data['win_percentage'] = round((player_data['total_wins'] / player_data['total_legs']) * 100, 1)
        else:
            player_data['win_percentage'] = 0
            
        if player_data['total_checkout_opportunities'] > 0:
            player_data['checkout_percentage'] = round((player_data['total_checkouts_hit'] / player_data['total_checkout_opportunities']) * 100, 1)
        else:
            player_data['checkout_percentage'] = 0
    
    results['success'] = results['successful_matches'] > 0
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"event_scrape_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print(f"🎉 SCRAPE COMPLETE!")
    print(f"✅ Successful matches: {results['successful_matches']}")
    print(f"❌ Failed matches: {results['failed_matches']}")
    print(f"👥 Total players: {len(results['all_players'])}")
    print(f"💾 Results saved to: {filename}")
    print("="*80)
    
    return results


if __name__ == "__main__":
    # Test with AADS Event #1
    event_url = "https://tv.dartconnect.com/event/mt_joe6163l_1"
    event_name = "Atlantic Amateur Dart Series Event #1"
    
    results = scrape_full_event_comprehensive(event_url, event_name)
    
    if results['success']:
        print(f"\nTop 5 Players by Average:")
        sorted_players = sorted(
            results['all_players'].items(), 
            key=lambda x: x[1]['overall_average'], 
            reverse=True
        )
        
        for i, (name, stats) in enumerate(sorted_players[:5], 1):
            print(f"{i}. {name}: {stats['overall_average']} avg, {stats['total_180s']} x 180s, {stats['total_matches']} matches")
    else:
        print(f"❌ Scrape failed: {results.get('error', 'Unknown error')}")