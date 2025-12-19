"""
DartConnect Turn-by-Turn Scraper using Selenium
Extracts turn-by-turn data from JavaScript-rendered tables
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

def scrape_turn_by_turn_selenium(match_url):
    """
    Use Selenium to scrape turn-by-turn data from rendered JavaScript tables.
    """
    print(f"Launching browser to scrape: {match_url}\n")
    
    # Setup Chrome with webdriver-manager (auto-downloads ChromeDriver)
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # New headless mode
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    
    try:
        print("Loading page...")
        driver.get(match_url)
        
        # Wait for tables to load (turn_stats rows)
        print("Waiting for turn data to render...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "turn_stats"))
        )
        time.sleep(3)  # Extra wait for JavaScript rendering
        
        print("✅ Page loaded, extracting turn data...\n")
        
        # Extract player names from header
        try:
            home_element = driver.find_element(By.CSS_SELECTOR, "div:has(> .text-right) h2")
            away_element = driver.find_element(By.CSS_SELECTOR, "div:has(> .text-left) h2")
            home_player = home_element.text.strip()
            away_player = away_element.text.strip()
        except:
            home_player = "Player 1"
            away_player = "Player 2"
        
        match_data = {
            'match_url': match_url,
            'home_player': home_player,
            'away_player': away_player,
            'games': []
        }
        
        # Find all turn_stats rows
        turn_rows = driver.find_elements(By.CSS_SELECTOR, "tr.turn_stats")
        print(f"Found {len(turn_rows)} turn rows\n")
        
        if not turn_rows:
            print("❌ No turn_stats rows found - page may not have rendered correctly")
            return match_data
        
        current_leg = {
            'leg': 1,
            'home_player': home_player,
            'away_player': away_player,
            'starting_player': None,
            'checkout_player': None,
            'checkout_score': 0,
            'home_darts_used': 0,
            'away_darts_used': 0,
            'turns': []
        }
        
        # Determine starting player by finding green background on first row
        first_row = turn_rows[0] if turn_rows else None
        if first_row:
            try:
                # Check for green background on remaining scores (bg-[#...] with green color)
                left_remaining = first_row.find_element(By.CSS_SELECTOR, "td.score-holder.text-center:first-of-type")
                right_remaining = first_row.find_element(By.CSS_SELECTOR, "td.score-holder.text-center:last-of-type")
                
                left_bg = left_remaining.value_of_css_property("background-color")
                right_bg = right_remaining.value_of_css_property("background-color")
                
                # Green is typically rgb(0, 128, 0) or similar
                if "rgb(0, 128, 0)" in left_bg or "green" in left_bg.lower():
                    current_leg['starting_player'] = home_player
                    print(f"✅ Starting player: {home_player} (left/home)")
                elif "rgb(0, 128, 0)" in right_bg or "green" in right_bg.lower():
                    current_leg['starting_player'] = away_player
                    print(f"✅ Starting player: {away_player} (right/away)")
            except Exception as e:
                print(f"  Could not determine starting player: {e}")
        
        for row in turn_rows:
            try:
                # Find score cells using the CSS classes identified
                left_score_cell = row.find_element(By.CSS_SELECTOR, "td.cricketDarts.text-right")
                right_score_cell = row.find_element(By.CSS_SELECTOR, "td.cricketDarts.text-left")
                
                # Extract score values
                left_score_text = left_score_cell.text.strip()
                right_score_text = right_score_cell.text.strip()
                
                # Convert to integers - handle special cases:
                # 'x' or 'X' = bust (0 points, 3 darts used)
                # 'Ø' = miss (0 points, 3 darts used)
                # Empty = no throw yet (skip)
                def parse_score(text):
                    if not text:
                        return None  # Empty cell, no throw
                    if text.lower() == 'x' or text == 'Ø' or text == 'ø':
                        return 0  # Bust or miss = 0 points but 3 darts used
                    if text.isdigit():
                        return int(text)
                    return None
                
                left_score = parse_score(left_score_text)
                right_score = parse_score(right_score_text)
                
                # Get remaining scores (middle cells with score-holder class)
                score_holders = row.find_elements(By.CSS_SELECTOR, "td.score-holder.text-center")
                left_remaining = 0
                right_remaining = 0
                
                if len(score_holders) >= 2:
                    try:
                        left_remaining_text = score_holders[0].text.strip()
                        right_remaining_text = score_holders[-1].text.strip()
                        
                        left_remaining = int(left_remaining_text) if left_remaining_text.isdigit() else 0
                        right_remaining = int(right_remaining_text) if right_remaining_text.isdigit() else 0
                        
                        # Check for red background (game end with 0 remaining)
                        left_bg = score_holders[0].value_of_css_property("background-color")
                        right_bg = score_holders[-1].value_of_css_property("background-color")
                        
                        # Red is typically rgb(255, 0, 0) or similar
                        if "red" in left_bg.lower() or "rgb(255" in left_bg:
                            if left_remaining == 0:
                                current_leg['checkout_player'] = home_player
                                current_leg['checkout_score'] = left_score
                                print(f"  🎯 Checkout: {home_player} finished with {left_score}")
                        
                        if "red" in right_bg.lower() or "rgb(255" in right_bg:
                            if right_remaining == 0:
                                current_leg['checkout_player'] = away_player
                                current_leg['checkout_score'] = right_score
                                print(f"  🎯 Checkout: {away_player} finished with {right_score}")
                    except:
                        pass
                
                # Store turn data based on starting player
                # If home/left starts: read left-to-right
                # If away/right starts: read right-to-left
                if current_leg['starting_player'] == home_player:
                    # Home player starts, alternate home → away
                    turn_num = len(current_leg['turns']) + 1
                    if turn_num % 2 == 1:  # Odd turns = home player
                        turn_data = {
                            'round': (turn_num + 1) // 2,
                            'player': home_player,
                            'score': left_score,
                            'remaining': left_remaining
                        }
                    else:  # Even turns = away player
                        turn_data = {
                            'round': turn_num // 2,
                            'player': away_player,
                            'score': right_score,
                            'remaining': right_remaining
                        }
                else:
                    # Away player starts, alternate away → home
                    turn_num = len(current_leg['turns']) + 1
                    if turn_num % 2 == 1:  # Odd turns = away player
                        turn_data = {
                            'round': (turn_num + 1) // 2,
                            'player': away_player,
                            'score': right_score,
                            'remaining': right_remaining
                        }
                    else:  # Even turns = home player
                        turn_data = {
                            'round': turn_num // 2,
                            'player': home_player,
                            'score': left_score,
                            'remaining': left_remaining
                        }
                
                current_leg['turns'].append(turn_data)
                
            except Exception as e:
                print(f"  Warning: Could not parse row - {e}")
                continue
        
        if current_leg['turns']:
            # Extract exact dart counts
            try:
                # Find span.text-[#811].text-xl elements (exact darts for finishing player)
                dart_count_elements = driver.find_elements(By.CSS_SELECTOR, "span.text-xl[class*='text-[#']")
                
                for element in dart_count_elements:
                    dart_text = element.text.strip()
                    if dart_text.isdigit():
                        # This is the finishing player's exact dart count
                        exact_darts = int(dart_text)
                        if current_leg['checkout_player']:
                            if current_leg['checkout_player'] == home_player:
                                current_leg['home_darts_used'] = exact_darts
                                # Calculate non-finisher darts: rounds * 3
                                away_rounds = len([t for t in current_leg['turns'] if t['player'] == away_player])
                                current_leg['away_darts_used'] = away_rounds * 3
                            else:
                                current_leg['away_darts_used'] = exact_darts
                                home_rounds = len([t for t in current_leg['turns'] if t['player'] == home_player])
                                current_leg['home_darts_used'] = home_rounds * 3
                        break
            except Exception as e:
                print(f"  Could not extract exact dart counts: {e}")
                # Fallback: calculate based on turns
                home_turns = len([t for t in current_leg['turns'] if t['player'] == home_player])
                away_turns = len([t for t in current_leg['turns'] if t['player'] == away_player])
                current_leg['home_darts_used'] = home_turns * 3
                current_leg['away_darts_used'] = away_turns * 3
            
            match_data['games'].append(current_leg)
        
        return match_data
        
    finally:
        driver.quit()


def calculate_advanced_stats(turn_by_turn_data):
    """
    Calculate advanced statistics from turn-by-turn data.
    Now uses player-specific turn data instead of home/away columns.
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
            'total_darts': 0,
            'three_dart_average': 0,
            'first_9_average': 0,
            'checkouts': []
        },
        away_player: {
            'scores': [],
            '180s': 0,
            '140_plus': 0,
            '100_plus': 0,
            'first_9_scores': [],
            'total_darts': 0,
            'three_dart_average': 0,
            'first_9_average': 0,
            'checkouts': []
        }
    }
    
    for game in turn_by_turn_data['games']:
        # Track checkout for this leg
        checkout_player = game.get('checkout_player')
        checkout_score = game.get('checkout_score', 0)
        
        if checkout_player and checkout_score > 0:
            stats[checkout_player]['checkouts'].append(checkout_score)
        
        # Use exact dart counts if available
        home_darts = game.get('home_darts_used', 0)
        away_darts = game.get('away_darts_used', 0)
        
        if home_darts > 0:
            stats[home_player]['total_darts'] += home_darts
        if away_darts > 0:
            stats[away_player]['total_darts'] += away_darts
        
        for turn in game['turns']:
            player = turn['player']
            score = turn['score']
            
            # Collect all scores (including 0s)
            stats[player]['scores'].append(score)
            
            # Count special scores (only > 0)
            if score == 180:
                stats[player]['180s'] += 1
            if score >= 140:
                stats[player]['140_plus'] += 1
            if score >= 100:
                stats[player]['100_plus'] += 1
            
            # First 9 darts (3 turns)
            if len(stats[player]['first_9_scores']) < 3:
                stats[player]['first_9_scores'].append(score)
    
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
        
        # Checkout stats
        if stats[player]['checkouts']:
            stats[player]['checkout_average'] = sum(stats[player]['checkouts']) / len(stats[player]['checkouts'])
            stats[player]['high_checkout'] = max(stats[player]['checkouts'])
        else:
            stats[player]['checkout_average'] = 0
            stats[player]['high_checkout'] = 0
    
    return stats


if __name__ == "__main__":
    # Match 2 from Event 1
    match_url = "https://recap.dartconnect.com/matches/688e09b7f4fc02e124e7187f"
    
    print("=" * 80)
    print("MATCH 2 VERIFICATION TEST")
    print("=" * 80)
    print("Expected Results:")
    print("  - Miguel Velasquez: 54.55 average")
    print("  - Steve Rushton: 54.60 average")
    print("  - Rushton won 3-2")
    print("  - High finish: Miguel 35, Steve 32")
    print()
    print("📝 Score notation:")
    print("   x or X = Bust (0 points, 3 darts)")
    print("   Ø = Miss (0 points, 3 darts)")
    print("   (All turns count toward dart total for accurate averages)\n")
    
    try:
        # Scrape turn-by-turn data
        turn_data = scrape_turn_by_turn_selenium(match_url)
        
        print("=" * 80)
        print(f"✅ Scraped {len(turn_data['games'])} game(s)")
        print(f"   {turn_data['home_player']} vs {turn_data['away_player']}")
        
        if turn_data['games']:
            total_turns = sum(len(game['turns']) for game in turn_data['games'])
            print(f"   Total turns: {total_turns}")
            
            # Calculate statistics
            stats = calculate_advanced_stats(turn_data)
            
            print("\n" + "=" * 80)
            print("ADVANCED STATISTICS (180s, 140+, 100+, First 9)")
            print("=" * 80)
            
            for player, data in stats.items():
                print(f"\n{player}:")
                print(f"  3-Dart Average: {data['three_dart_average']:.2f}")
                print(f"  First 9 Average: {data['first_9_average']:.2f}")
                print(f"  180s: {data['180s']}")
                print(f"  140+ scores: {data['140_plus']}")
                print(f"  100+ scores: {data['100_plus']}")
                print(f"  Checkouts: {len(data['checkouts'])} (avg: {data['checkout_average']:.1f}, high: {data['high_checkout']})")
                print(f"  Total turns: {len(data['scores'])}")
                print(f"  First 10 scores: {data['scores'][:10]}")
            
            # Save results
            with open('turn_by_turn_selenium.json', 'w') as f:
                json.dump(turn_data, f, indent=2)
            print("\n✅ Saved to: turn_by_turn_selenium.json")
            
            with open('advanced_stats_selenium.json', 'w') as f:
                json.dump(stats, f, indent=2)
            print("✅ Saved stats to: advanced_stats_selenium.json")
        else:
            print("\n❌ No game data found")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
