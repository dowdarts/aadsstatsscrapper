#!/usr/bin/env python3
"""
Updated DartConnect Scraper - HTML Parser Version
Handles the new DartConnect API that returns HTML with embedded JSON data
"""

import requests
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
import html

def extract_match_urls_from_event(event_url):
    """
    Extract match URLs from an event using the DartConnect API2 endpoint
    """
    print(f"🎯 Extracting match URLs from: {event_url}")
    
    # Extract event ID from URL
    event_id_pattern = r'/event/([^/]+)'
    event_id_match = re.search(event_id_pattern, event_url)
    if not event_id_match:
        print(f"❌ Could not extract event ID from URL: {event_url}")
        return []
    
    event_id = event_id_match.group(1)
    print(f"📋 Event ID: {event_id}")
    
    # Use API2 endpoint to get match data
    api_url = f"https://tv.dartconnect.com/api2/event/{event_id}/matches"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🔗 Fetching from API: {api_url}")
        response = requests.post(api_url, headers=headers, json={})
        response.raise_for_status()
        
        api_data = response.json()
        print(f"🔍 Debug - API response keys: {list(api_data.keys()) if api_data else 'None'}")
        
        if not api_data:
            print(f"❌ No API response data")
            return []
        
        if 'payload' not in api_data:
            print(f"❌ No 'payload' key in API response. Available keys: {list(api_data.keys())}")
            return []
        
        # Access the matches from the nested structure
        payload = api_data['payload']
        print(f"🔍 Debug - Payload keys: {list(payload.keys()) if isinstance(payload, dict) else 'Payload is not a dict'}")
        
        # Check for matches in 'completed' field (based on PowerShell output)
        matches = []
        if 'completed' in payload and isinstance(payload['completed'], list):
            matches = payload['completed']
        
        if not matches:
            print(f"❌ No matches found in API response")
            print(f"🔍 Debug - Looking for matches in: {payload.keys()}")
            return []
        print(f"✅ Found {len(matches)} matches in event")
        
        match_urls = []
        for match in matches:
            if 'mi' in match:  # 'mi' is the match_id field in the API response
                match_id = match['mi']
                match_url = f"https://recap.dartconnect.com/players/{match_id}"
                match_urls.append(match_url)
                print(f"  📄 Match: {match_id}")
        
        return match_urls
        
    except Exception as e:
        print(f"❌ Error fetching match URLs: {str(e)}")
        return []

def parse_html_data_page(html_content):
    """
    Extract JSON data from the HTML data-page attribute
    """
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the div with data-page attribute
        app_div = soup.find('div', {'id': 'app'})
        if not app_div or 'data-page' not in app_div.attrs:
            print("❌ Could not find data-page attribute in HTML")
            return None
        
        # Extract and decode the JSON data
        data_page = app_div['data-page']
        # Decode HTML entities
        data_page = html.unescape(data_page)
        # Parse JSON
        page_data = json.loads(data_page)
        
        return page_data
        
    except Exception as e:
        print(f"❌ Error parsing HTML data-page: {str(e)}")
        return None

def scrape_single_match_comprehensive(match_url):
    """
    Scrape comprehensive data from a single match URL by parsing HTML data
    """
    print(f"🎯 Scraping match: {match_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    try:
        # Get players data
        print(f"  📊 Fetching player data...")
        response = requests.get(match_url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML data
        page_data = parse_html_data_page(response.text)
        if not page_data:
            print(f"  ❌ Could not parse page data")
            return None
        
        # Extract match info
        props = page_data.get('props', {})
        match_info = props.get('matchInfo', {})
        players_data = props.get('players', [])
        
        if not match_info:
            print(f"  ❌ No match info found")
            return None
        
        print(f"  ✅ Found match: {match_info.get('competition_title', 'Unknown')} - {match_info.get('event_title', 'Unknown')}")
        
        # Get counts data
        counts_url = match_url.replace('/players/', '/counts/')
        print(f"  📈 Fetching counts data...")
        
        counts_response = requests.get(counts_url, headers=headers)
        counts_response.raise_for_status()
        
        counts_page_data = parse_html_data_page(counts_response.text)
        if counts_page_data:
            counts_props = counts_page_data.get('props', {})
            player_performances = counts_props.get('playerPerformances', [])
        else:
            player_performances = []
        
        # Extract match ID
        match_id = match_info.get('id', match_url.split('/')[-1])
        
        # Build comprehensive match data
        match_data = {
            'match_id': match_id,
            'competition_title': match_info.get('competition_title', ''),
            'event_title': match_info.get('event_title', ''),
            'match_date': match_info.get('server_match_start_date', ''),
            'match_time': match_info.get('match_start_date', ''),
            'total_sets': match_info.get('total_sets', 0),
            'total_games': match_info.get('total_games', 0),
            'game_time': match_info.get('game_time', ''),
            'players': []
        }
        
        # Process player data
        opponents = match_info.get('opponents', [])
        
        for i, opponent in enumerate(opponents):
            player_data = {
                'name': opponent.get('name', f'Player {i+1}'),
                'score': opponent.get('score', 0),
                'set_wins': opponent.get('set_wins', 0),
                'leg_wins': opponent.get('leg_wins', 0),
                'points_scored_ppr': opponent.get('points_scored_ppr', '0').replace(',', ''),
                'darts_thrown_ppr': opponent.get('darts_thrown_ppr', '0'),
                'ppr': opponent.get('ppr', '0'),
                'win_percentage': 0,  # Calculate later
                '180s': 0,  # Will be filled from performance data
                'checkout_percentage': 0,  # Will be filled from performance data
                'highest_checkout': 0,  # Will be filled from performance data
                'first_nine_average': 0  # Will be filled from performance data
            }
            
            # Calculate win percentage
            if match_data['total_games'] > 0:
                player_data['win_percentage'] = round((opponent.get('leg_wins', 0) / match_data['total_games']) * 100, 2)
            
            # Add performance data if available
            for perf in player_performances:
                if perf.get('name', '').lower() in player_data['name'].lower() or player_data['name'].lower() in perf.get('name', '').lower():
                    # Extract 180s
                    dist_data = perf.get('dist', {})
                    plus_100 = dist_data.get('plus_100', {})
                    if plus_100.get('180') and plus_100['180'] != '-':
                        player_data['180s'] = plus_100['180']
                    
                    # Extract checkout data
                    player_data['checkout_percentage'] = perf.get('coe', '0%').replace('%', '')
                    
                    double_out_stats = perf.get('double_out_stats', {})
                    if double_out_stats.get('highest'):
                        player_data['highest_checkout'] = double_out_stats['highest']
                    
                    # Extract first nine average
                    if perf.get('first_nine'):
                        try:
                            player_data['first_nine_average'] = float(perf['first_nine'])
                        except (ValueError, TypeError):
                            pass
                    
                    break
            
            match_data['players'].append(player_data)
        
        print(f"  ✅ Match data extracted successfully")
        print(f"    🏆 {match_data['competition_title']}")
        print(f"    📅 {match_data['match_date']}")
        print(f"    👥 Players: {', '.join([p['name'] for p in match_data['players']])}")
        
        return match_data
        
    except Exception as e:
        print(f"  ❌ Error scraping match: {str(e)}")
        return None

def scrape_event_comprehensive(event_url):
    """
    Scrape all matches from an event URL and return comprehensive data
    """
    print(f"\n🚀 Starting comprehensive event scraping...")
    print(f"🎯 Event URL: {event_url}")
    
    # Step 1: Extract match URLs
    match_urls = extract_match_urls_from_event(event_url)
    if not match_urls:
        print("❌ No match URLs found")
        return None
    
    print(f"\n📊 Found {len(match_urls)} matches to scrape")
    
    # Step 2: Scrape each match
    all_matches = []
    successful_matches = 0
    
    for i, match_url in enumerate(match_urls, 1):
        print(f"\n🔄 Processing match {i}/{len(match_urls)}")
        
        match_data = scrape_single_match_comprehensive(match_url)
        if match_data:
            all_matches.append(match_data)
            successful_matches += 1
        else:
            print(f"  ⚠️ Failed to scrape match")
    
    # Step 3: Compile results
    results = {
        'event_url': event_url,
        'scrape_timestamp': datetime.now().isoformat(),
        'total_matches_found': len(match_urls),
        'successfully_scraped': successful_matches,
        'matches': all_matches
    }
    
    print(f"\n🎉 Scraping completed!")
    print(f"✅ Successfully scraped: {successful_matches}/{len(match_urls)} matches")
    
    return results

if __name__ == "__main__":
    # Test with the Event #1 URL
    event_url = "https://tv.dartconnect.com/event/mt_joe6163l_1"
    
    print("🎯 Testing HTML Parser Scraper")
    print("=" * 50)
    
    results = scrape_event_comprehensive(event_url)
    
    if results:
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"event_scrape_results_html_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Print summary
        print(f"\n📋 SUMMARY:")
        print(f"🎯 Event URL: {results['event_url']}")
        print(f"📅 Scraped: {results['scrape_timestamp']}")
        print(f"🔍 Matches Found: {results['total_matches_found']}")
        print(f"✅ Successfully Scraped: {results['successfully_scraped']}")
        
        if results['matches']:
            print(f"\n👥 PLAYERS FOUND:")
            all_players = set()
            for match in results['matches']:
                for player in match['players']:
                    all_players.add(player['name'])
            
            for player in sorted(all_players):
                print(f"  - {player}")
    else:
        print("❌ Failed to scrape event data")