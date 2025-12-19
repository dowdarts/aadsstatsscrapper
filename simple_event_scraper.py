#!/usr/bin/env python3
"""
AADS Event Scraper - Simple Two-Stage Approach
1. Input event URL → Extract match URLs 
2. Scrape each match URL → Get detailed stats
3. Aggregate and save results

Usage:
    python simple_event_scraper.py
    
Enter event URL when prompted.
"""

import requests
import json
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import time
from typing import Dict, List
from datetime import datetime
from bs4 import BeautifulSoup


def extract_match_urls_from_event(event_url: str) -> List[str]:
    """
    STAGE 1: Extract all match URLs from a DartConnect event page
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
        with urlopen(request_obj) as response:
            data = json.load(response)
            
        print(f"✅ API2 response received")
        
        # Extract match URLs
        match_urls = []
        
        if 'payload' in data and 'completed' in data['payload']:
            matches = data['payload']['completed']
            print(f"Found {len(matches)} completed matches")
            
            for match in matches:
                match_id = match.get('id')
                if match_id:
                    match_url = f"https://recap.dartconnect.com/{match_id}"
                    match_urls.append(match_url)
        
        print(f"✅ Extracted {len(match_urls)} match URLs")
        return match_urls
        
    except Exception as e:
        print(f"❌ API2 failed: {e}")
        raise


def scrape_match_stats(match_url: str) -> Dict:
    """
    STAGE 2: Scrape stats from individual match recap page
    """
    match_id = match_url.split('/')[-1]
    print(f"  📊 Scraping match: {match_id}")
    
    result = {
        'match_id': match_id,
        'match_url': match_url,
        'players': [],
        'success': False,
        'errors': []
    }
    
    try:
        # Try the players endpoint for comprehensive stats
        players_url = f"https://recap.dartconnect.com/players/{match_id}"
        response = requests.get(players_url, timeout=10)
        response.raise_for_status()
        
        # Parse HTML and extract JSON data
        soup = BeautifulSoup(response.text, 'html.parser')
        app_div = soup.find('div', {'id': 'app'})
        
        if not app_div or 'data-page' not in app_div.attrs:
            result['errors'].append("No data found in page")
            return result
        
        # Extract Inertia.js data
        data_page = app_div['data-page']
        page_data = json.loads(data_page)
        props = page_data.get('props', {})
        
        # Extract player data
        if 'page' in props and 'players' in props['page']:
            for player_data in props['page']['players']:
                player = {
                    'name': player_data.get('player_name', ''),
                    'legs_played': player_data.get('total_games', 0),
                    'legs_won': player_data.get('total_wins', 0),
                    'darts_thrown': player_data.get('darts_thrown', 0),
                    'points_scored': player_data.get('points_scored', 0),
                    'average': player_data.get('average', 0),
                    'first_nine_avg': player_data.get('first_nine_avg'),
                    'highest_score': player_data.get('highest_score'),
                    'win_percentage': player_data.get('win_percentage', 0),
                }
                
                result['players'].append(player)
        
        # Try to get additional stats from counts endpoint
        counts_url = f"https://recap.dartconnect.com/counts/{match_id}"
        try:
            counts_response = requests.get(counts_url, timeout=10)
            counts_response.raise_for_status()
            
            counts_soup = BeautifulSoup(counts_response.text, 'html.parser')
            counts_app_div = counts_soup.find('div', {'id': 'app'})
            
            if counts_app_div and 'data-page' in counts_app_div.attrs:
                counts_data_page = counts_app_div['data-page']
                counts_page_data = json.loads(counts_data_page)
                counts_props = counts_page_data.get('props', {})
                
                if 'page' in counts_props and 'players' in counts_props['page']:
                    # Map counts data to existing players
                    for counts_player in counts_props['page']['players']:
                        player_name = counts_player.get('player_name', '')
                        
                        # Find matching player in results
                        for player in result['players']:
                            if player['name'] == player_name:
                                player['count_180s'] = counts_player.get('count_180s', 0)
                                player['count_140_plus'] = counts_player.get('count_140_plus', 0)
                                player['count_100_plus'] = counts_player.get('count_100_plus', 0)
                                player['checkout_opportunities'] = counts_player.get('checkout_opportunities', 0)
                                player['checkouts_hit'] = counts_player.get('checkouts_hit', 0)
                                player['checkout_percentage'] = counts_player.get('checkout_efficiency', 0)
                                player['highest_checkout'] = counts_player.get('highest_checkout')
                                break
        except:
            # Counts data is optional - don't fail if we can't get it
            pass
        
        result['success'] = len(result['players']) > 0
        
        if result['success']:
            print(f"    ✅ Found {len(result['players'])} players")
        else:
            print(f"    ❌ No players found")
            result['errors'].append("No players found")
        
        return result
        
    except Exception as e:
        result['errors'].append(str(e))
        print(f"    ❌ Error: {e}")
        return result


def scrape_event_complete(event_url: str, event_name: str = "AADS Event") -> Dict:
    """
    Complete event scraper - combines both stages
    """
    print(f"\n🚀 STARTING EVENT SCRAPE")
    print(f"Event: {event_name}")
    print(f"URL: {event_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {
        'event_name': event_name,
        'event_url': event_url,
        'scraped_at': datetime.now().isoformat(),
        'total_matches': 0,
        'successful_matches': 0,
        'failed_matches': 0,
        'players': {},  # Aggregated stats
        'matches': [],  # Individual match details
        'errors': []
    }
    
    try:
        # STAGE 1: Get match URLs
        match_urls = extract_match_urls_from_event(event_url)
        if not match_urls:
            results['errors'].append('No matches found in event')
            return results
        
        results['total_matches'] = len(match_urls)
        
        # STAGE 2: Scrape each match
        print(f"\n🔍 STAGE 2: Scraping {len(match_urls)} matches")
        print("="*60)
        
        for i, match_url in enumerate(match_urls, 1):
            print(f"\n📋 Match {i}/{len(match_urls)}")
            
            match_result = scrape_match_stats(match_url)
            results['matches'].append(match_result)
            
            if match_result['success']:
                results['successful_matches'] += 1
                
                # Aggregate player stats
                for player in match_result['players']:
                    name = player['name']
                    if name not in results['players']:
                        results['players'][name] = {
                            'name': name,
                            'total_matches': 0,
                            'total_legs': 0,
                            'total_wins': 0,
                            'total_darts': 0,
                            'total_points': 0,
                            'total_180s': 0,
                            'total_140_plus': 0,
                            'total_100_plus': 0,
                            'highest_checkout': 0,
                            'match_history': []
                        }
                    
                    # Add to totals
                    p = results['players'][name]
                    p['total_matches'] += 1
                    p['total_legs'] += player.get('legs_played', 0)
                    p['total_wins'] += player.get('legs_won', 0)
                    p['total_darts'] += player.get('darts_thrown', 0)
                    p['total_points'] += int(str(player.get('points_scored', 0)).replace(',', ''))
                    p['total_180s'] += player.get('count_180s', 0)
                    p['total_140_plus'] += player.get('count_140_plus', 0)
                    p['total_100_plus'] += player.get('count_100_plus', 0)
                    
                    if player.get('highest_checkout'):
                        p['highest_checkout'] = max(p['highest_checkout'], player.get('highest_checkout', 0))
                    
                    # Store match details
                    p['match_history'].append({
                        'match_id': match_result['match_id'],
                        'legs': player.get('legs_played', 0),
                        'wins': player.get('legs_won', 0),
                        'average': player.get('average', 0),
                        'count_180s': player.get('count_180s', 0)
                    })
            else:
                results['failed_matches'] += 1
                results['errors'].extend(match_result['errors'])
            
            # Rate limiting
            if i < len(match_urls):
                time.sleep(1)
        
        # Calculate final averages
        for player_data in results['players'].values():
            if player_data['total_darts'] > 0:
                player_data['overall_average'] = round(player_data['total_points'] / player_data['total_darts'] * 3, 2)
            else:
                player_data['overall_average'] = 0
                
            if player_data['total_legs'] > 0:
                player_data['win_percentage'] = round((player_data['total_wins'] / player_data['total_legs']) * 100, 1)
            else:
                player_data['win_percentage'] = 0
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"event_scrape_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n" + "="*60)
        print(f"🎉 SCRAPE COMPLETE!")
        print(f"✅ Successful: {results['successful_matches']}/{results['total_matches']} matches")
        print(f"👥 Players found: {len(results['players'])}")
        print(f"💾 Saved to: {filename}")
        
        # Show top players
        if results['players']:
            print(f"\n🏆 TOP PLAYERS:")
            sorted_players = sorted(
                results['players'].items(), 
                key=lambda x: x[1]['overall_average'], 
                reverse=True
            )
            
            for i, (name, stats) in enumerate(sorted_players[:5], 1):
                print(f"  {i}. {name}: {stats['overall_average']} avg, {stats['total_180s']} x 180s, {stats['total_matches']} matches")
        
        print("="*60)
        
        return results
        
    except Exception as e:
        results['errors'].append(f"Event scrape failed: {str(e)}")
        print(f"❌ Event scrape failed: {e}")
        return results


def main():
    """Interactive main function"""
    print("🎯 AADS Event Scraper")
    print("="*40)
    
    # Get event URL from user
    event_url = input("Enter DartConnect event URL: ").strip()
    
    if not event_url:
        event_url = "https://tv.dartconnect.com/event/mt_joe6163l_1"  # Default to Event #1
        print(f"Using default: {event_url}")
    
    event_name = input("Enter event name (optional): ").strip()
    if not event_name:
        event_name = "AADS Event"
    
    # Run scraper
    results = scrape_event_complete(event_url, event_name)
    
    if results['successful_matches'] > 0:
        print(f"\n✅ Success! Scraped {results['successful_matches']} matches")
        return results
    else:
        print(f"\n❌ Failed to scrape any matches")
        if results['errors']:
            print("Errors:")
            for error in results['errors']:
                print(f"  - {error}")
        return None


if __name__ == "__main__":
    main()