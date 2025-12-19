"""
Scrape Player Performance and Match Counts tabs directly from DartConnect
No manual HTML saving needed!
"""

import requests
from bs4 import BeautifulSoup
import json
import html

def scrape_tab_data(match_id):
    """
    Scrape both Player Performance and Match Counts tabs for a match.
    
    Args:
        match_id: DartConnect match ID (e.g., "688e09b7f4fc02e124e7187f")
    
    Returns:
        dict with player_performance and match_counts data
    """
    base_url = "https://recap.dartconnect.com"
    
    # URLs for different tabs
    players_url = f"{base_url}/players/{match_id}"
    counts_url = f"{base_url}/counts/{match_id}"
    
    result = {
        'match_id': match_id,
        'player_performance': None,
        'match_counts': None,
        'errors': []
    }
    
    # Fetch Player Performance tab
    print(f"Fetching Player Performance: {players_url}")
    try:
        response = requests.get(players_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        app_div = soup.find('div', {'id': 'app'})
        
        if app_div and 'data-page' in app_div.attrs:
            page_data_str = html.unescape(app_div['data-page'])
            page_data = json.loads(page_data_str)
            props = page_data.get('props', {})
            
            result['player_performance'] = props
            print("✅ Player Performance data extracted")
        else:
            result['errors'].append("No Inertia.js data in Player Performance page")
            print("❌ No Inertia.js data found")
    except Exception as e:
        result['errors'].append(f"Player Performance error: {e}")
        print(f"❌ Error: {e}")
    
    # Fetch Match Counts tab
    print(f"\nFetching Match Counts: {counts_url}")
    try:
        response = requests.get(counts_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        app_div = soup.find('div', {'id': 'app'})
        
        if app_div and 'data-page' in app_div.attrs:
            page_data_str = html.unescape(app_div['data-page'])
            page_data = json.loads(page_data_str)
            props = page_data.get('props', {})
            
            result['match_counts'] = props
            print("✅ Match Counts data extracted")
        else:
            result['errors'].append("No Inertia.js data in Match Counts page")
            print("❌ No Inertia.js data found")
    except Exception as e:
        result['errors'].append(f"Match Counts error: {e}")
        print(f"❌ Error: {e}")
    
    return result


def parse_player_stats(tab_data):
    """Extract and format player statistics from both tabs"""
    
    players = {}
    
    # Parse Player Performance data
    if tab_data['player_performance']:
        perf_data = tab_data['player_performance']
        
        # Look for player data in various possible structures
        for key in ['players', 'stats', 'playerStats', 'data']:
            if key in perf_data:
                print(f"\nFound player data in key: {key}")
                print(json.dumps(perf_data[key], indent=2)[:500])
    
    # Parse Match Counts data
    if tab_data['match_counts']:
        counts_data = tab_data['match_counts']
        
        for key in ['counts', 'stats', 'matchCounts', 'data']:
            if key in counts_data:
                print(f"\nFound counts data in key: {key}")
                print(json.dumps(counts_data[key], indent=2)[:500])
    
    return players


if __name__ == "__main__":
    # Match 2 from Event 1
    match_id = "688e09b7f4fc02e124e7187f"
    
    print("=" * 80)
    print("SCRAPING DARTCONNECT TABS (NO MANUAL SAVE NEEDED)")
    print("=" * 80)
    print(f"Match ID: {match_id}")
    print()
    
    # Fetch data from both tabs
    tab_data = scrape_tab_data(match_id)
    
    # Save raw data
    with open('tab_data_raw.json', 'w') as f:
        json.dump(tab_data, f, indent=2)
    print("\n✅ Saved raw data to: tab_data_raw.json")
    
    # Parse and display stats
    print("\n" + "=" * 80)
    print("EXTRACTING STATISTICS")
    print("=" * 80)
    
    players = parse_player_stats(tab_data)
    
    if tab_data['errors']:
        print("\n⚠️  Errors encountered:")
        for error in tab_data['errors']:
            print(f"  - {error}")
    
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print("Expected:")
    print("  - Miguel Velasquez: 54.55 average")
    print("  - Steve Rushton: 54.60 average")
    print("  - Rushton won 3-2")
