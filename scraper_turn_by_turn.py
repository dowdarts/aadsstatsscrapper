"""
DartConnect Turn-by-Turn Scraper
Extracts individual turn scores from match recap HTML tables to calculate:
- 180s, 140+, 100+ scores
- Accurate first 9 average
- Visit-level analysis
"""

import requests
from bs4 import BeautifulSoup
import json
import html

def scrape_turn_by_turn_data(match_url):
    """
    Scrape turn-by-turn scoring data from DartConnect match recap page HTML table.
    The turn-by-turn data is NOT in Inertia props - it's rendered in HTML tables!
    
    Args:
        match_url: URL to match recap (e.g., https://recap.dartconnect.com/matches/688e66b6f4fc02e124e759c8)
    
    Returns:
        dict: Match data with turn-by-turn details for each game/leg
    """
    # NOTE: The page requires JavaScript to render the turn-by-turn tables
    # We need to use Selenium or parse the static HTML if available
    
    print("⚠️  WARNING: DartConnect uses JavaScript to render turn-by-turn tables")
    print("   The data visible in browser DevTools is NOT in the initial HTML response")
    print("   We need to use Selenium/Playwright to scrape rendered content\n")
    
    response = requests.get(match_url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Try to find turn data in HTML tables (may not exist without JS rendering)
    tables = soup.find_all('table', class_='w-full')
    print(f"Found {len(tables)} tables in HTML")
    
    # Parse Inertia.js data for player names
    app_div = soup.find('div', {'id': 'app'})
    if not app_div or 'data-page' not in app_div.attrs:
        raise ValueError("Could not find Inertia.js data in page")
    
    page_data_str = html.unescape(app_div['data-page'])
    page_data = json.loads(page_data_str)
    props = page_data.get('props', {})
    
    match_info = props.get('matchInfo', {})
    home_name = match_info.get('home', {}).get('name', 'Home')
    away_name = match_info.get('away', {}).get('name', 'Away')
    
    match_data = {
        'match_id': match_info.get('id'),
        'match_name': match_info.get('name'),
        'home_player': home_name,
        'away_player': away_name,
        'games': [],
        'note': 'Turn-by-turn data requires JavaScript rendering - use Selenium'
    }
    
    # Try to parse tables if they exist (they won't without JS)
    for table in tables:
        rows = table.find_all('tr', class_='turn_stats')
        if not rows:
            continue
            
        leg_info = {
            'game': 'unknown',
            'leg': 1,
            'home_player': home_name,
            'away_player': away_name,
            'turns': []
        }
        
        for row in rows:
            # Look for cricketDarts cells
            home_score_cell = row.find('td', class_='cricketDarts text-right')
            away_score_cell = row.find('td', class_='cricketDarts text-left')
            
            if home_score_cell and away_score_cell:
                turn_data = {
                    'home_score': int(home_score_cell.text.strip()) if home_score_cell.text.strip().isdigit() else 0,
                    'away_score': int(away_score_cell.text.strip()) if away_score_cell.text.strip().isdigit() else 0
                }
                leg_info['turns'].append(turn_data)
        
        if leg_info['turns']:
            match_data['games'].append(leg_info)
    
    return match_data


def calculate_advanced_stats(turn_by_turn_data):
    """
    Calculate advanced statistics from turn-by-turn data.
    
    Args:
        turn_by_turn_data: Output from scrape_turn_by_turn_data()
    
    Returns:
        dict: Player statistics including 180s, 140+, 100+, first 9 avg
    """
    home_player = turn_by_turn_data['home_player']
    away_player = turn_by_turn_data['away_player']
    
    stats = {
        home_player: {
            'scores': [],
            '180s': 0,
            '140_plus': 0,
            '100_plus': 0,
            'first_9_scores': [],
            'total_darts': 0
        },
        away_player: {
            'scores': [],
            '180s': 0,
            '140_plus': 0,
            '100_plus': 0,
            'first_9_scores': [],
            'total_darts': 0
        }
    }
    
    for game in turn_by_turn_data['games']:
        for turn in game['turns']:
            # Home player
            home_score = turn['home_score']
            if home_score:
                stats[home_player]['scores'].append(home_score)
                stats[home_player]['total_darts'] += 3  # Each turn is 3 darts
                
                # Count special scores
                if home_score == 180:
                    stats[home_player]['180s'] += 1
                if home_score >= 140:
                    stats[home_player]['140_plus'] += 1
                if home_score >= 100:
                    stats[home_player]['100_plus'] += 1
                
                # First 9 darts (3 turns)
                if len(stats[home_player]['first_9_scores']) < 3:
                    stats[home_player]['first_9_scores'].append(home_score)
            
            # Away player
            away_score = turn['away_score']
            if away_score:
                stats[away_player]['scores'].append(away_score)
                stats[away_player]['total_darts'] += 3
                
                if away_score == 180:
                    stats[away_player]['180s'] += 1
                if away_score >= 140:
                    stats[away_player]['140_plus'] += 1
                if away_score >= 100:
                    stats[away_player]['100_plus'] += 1
                
                if len(stats[away_player]['first_9_scores']) < 3:
                    stats[away_player]['first_9_scores'].append(away_score)
    
    # Calculate averages
    for player in [home_player, away_player]:
        if stats[player]['scores']:
            total_score = sum(stats[player]['scores'])
            total_darts = stats[player]['total_darts']
            stats[player]['three_dart_average'] = (total_score / total_darts * 3) if total_darts > 0 else 0
        
        if stats[player]['first_9_scores']:
            first_9_total = sum(stats[player]['first_9_scores'])
            first_9_darts = len(stats[player]['first_9_scores']) * 3
            stats[player]['first_9_average'] = (first_9_total / first_9_darts * 3) if first_9_darts > 0 else 0
    
    return stats


def scrape_and_analyze(match_url):
    """
    Complete pipeline: scrape turn data and calculate statistics.
    """
    print(f"Scraping turn-by-turn data from: {match_url}\n")
    
    turn_data = scrape_turn_by_turn_data(match_url)
    print(f"✅ Found {len(turn_data['games'])} games/legs\n")
    
    stats = calculate_advanced_stats(turn_data)
    
    # Display results
    print("=" * 80)
    print("ADVANCED STATISTICS")
    print("=" * 80)
    
    for player, data in stats.items():
        print(f"\n{player}:")
        print(f"  3-Dart Average: {data['three_dart_average']:.2f}")
        print(f"  First 9 Average: {data['first_9_average']:.2f}")
        print(f"  180s: {data['180s']}")
        print(f"  140+ scores: {data['140_plus']}")
        print(f"  100+ scores: {data['100_plus']}")
        print(f"  Total turns: {len(data['scores'])}")
        print(f"  All scores: {data['scores'][:10]}{'...' if len(data['scores']) > 10 else ''}")
    
    return turn_data, stats


if __name__ == "__main__":
    # Test with the match shown in screenshots
    match_url = "https://recap.dartconnect.com/matches/688e66b6f4fc02e124e759c8"
    
    try:
        turn_data, stats = scrape_and_analyze(match_url)
        
        # Save results
        with open('turn_by_turn_data.json', 'w') as f:
            json.dump(turn_data, f, indent=2)
        print("\n✅ Saved turn-by-turn data to: turn_by_turn_data.json")
        
        with open('advanced_stats_complete.json', 'w') as f:
            json.dump(stats, f, indent=2)
        print("✅ Saved advanced statistics to: advanced_stats_complete.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
