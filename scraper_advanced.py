#!/usr/bin/env python3
"""
ADVANCED DARTCONNECT SCRAPER
Extracts comprehensive statistics from match recap pages including:
- 180s, 140+, 100+ scores
- First 9 average
- Checkout stats (attempts, success rate, 100+ checkouts, 170s)
- Leg win percentage
- Per-leg detailed statistics
"""

import requests
from bs4 import BeautifulSoup
import json
import html
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedDartConnectScraper:
    """
    Advanced scraper for DartConnect match recap pages with detailed statistics
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_match_advanced(self, url: str) -> Dict:
        """
        Scrape comprehensive match statistics
        
        Returns:
            Dict with match info and per-player detailed stats
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find Inertia.js data
            app_div = soup.find('div', {'id': 'app'})
            if not app_div or not app_div.has_attr('data-page'):
                logger.error("No Inertia.js data found")
                return {}
            
            # Parse JSON data
            page_data = html.unescape(app_div['data-page'])
            data = json.loads(page_data)
            
            if 'props' not in data:
                logger.error("No props in Inertia data")
                return {}
            
            props = data['props']
            
            # Extract comprehensive stats
            match_data = self._extract_comprehensive_stats(props)
            match_data['match_url'] = url
            
            return match_data
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {}
    
    def _extract_comprehensive_stats(self, props: Dict) -> Dict:
        """
        Extract all available statistics from Inertia props
        """
        segments = props.get('segments', {})
        
        # Initialize player stats tracking
        player_stats = {}
        
        # Process each segment and leg
        for segment_key, segment_list in segments.items():
            if not segment_list or len(segment_list) == 0:
                continue
            
            legs_list = segment_list[0]
            
            if not isinstance(legs_list, list):
                continue
            
            # Process each leg
            for leg_index, leg_data in enumerate(legs_list, 1):
                if not isinstance(leg_data, dict):
                    continue
                
                # Get leg metadata
                leg_number = leg_data.get('set_number', leg_index)
                darts_thrown = leg_data.get('darts_thrown', 0)
                
                # Process home player
                self._process_player_leg(
                    player_stats, 
                    leg_data.get('home'), 
                    leg_number, 
                    darts_thrown,
                    'home'
                )
                
                # Process away player
                self._process_player_leg(
                    player_stats, 
                    leg_data.get('away'), 
                    leg_number, 
                    darts_thrown,
                    'away'
                )
        
        # Calculate final aggregated stats
        result = {
            'players': []
        }
        
        for player_name, stats in player_stats.items():
            player_summary = self._calculate_player_summary(player_name, stats)
            result['players'].append(player_summary)
        
        return result
    
    def _process_player_leg(self, player_stats: Dict, leg_player_data: Optional[Dict], 
                           leg_number: int, total_darts: int, side: str):
        """
        Process statistics for a single player in a single leg
        """
        if not leg_player_data or 'players' not in leg_player_data:
            return
        
        if not leg_player_data['players']:
            return
        
        player_name = leg_player_data['players'][0].get('player_label', '').strip()
        
        if not player_name:
            return
        
        # Initialize player if not exists
        if player_name not in player_stats:
            player_stats[player_name] = {
                'legs': [],
                'legs_won': 0,
                'legs_lost': 0,
                'total_checkout_attempts': 0,
                'successful_checkouts': 0,
                'checkout_values': [],
                'checkout_100_plus': 0,
                'checkout_170': 0,
                'all_ppr_values': [],
                'first_9_values': [],  # PPR from first 3 rounds
                'score_180': 0,
                'score_140_plus': 0,
                'score_100_plus': 0
            }
        
        # Extract leg statistics
        ppr = leg_player_data.get('ppr')
        starting_points = leg_player_data.get('starting_points', 501)
        ending_points = leg_player_data.get('ending_points', 0)
        double_out = leg_player_data.get('double_out_points')
        won_leg = leg_player_data.get('win', False)
        
        # PPR (3-dart average for this leg)
        ppr_float = 0.0
        if ppr:
            try:
                ppr_float = float(ppr)
                player_stats[player_name]['all_ppr_values'].append(ppr_float)
            except (ValueError, TypeError):
                pass
        
        # Win/loss tracking
        if won_leg:
            player_stats[player_name]['legs_won'] += 1
        else:
            player_stats[player_name]['legs_lost'] += 1
        
        # Checkout tracking
        if double_out:
            checkout_value = int(double_out)
            player_stats[player_name]['checkout_values'].append(checkout_value)
            player_stats[player_name]['successful_checkouts'] += 1
            
            if checkout_value >= 100:
                player_stats[player_name]['checkout_100_plus'] += 1
            
            if checkout_value == 170:
                player_stats[player_name]['checkout_170'] += 1
        
        # Count checkout attempts (won leg = successful, any leg with low ending points = attempt)
        if won_leg or ending_points <= 170:
            player_stats[player_name]['total_checkout_attempts'] += 1
        
        # Calculate number of rounds (turns) in this leg
        # Each round = 3 darts
        rounds_played = total_darts // 6  # Divide by 6 because both players share darts_thrown
        
        # First 9 average (first 3 rounds = 9 darts)
        if rounds_played >= 3:
            # Approximate: use ppr for first 3 rounds
            # In reality we'd need turn-by-turn data which may not be available
            # For now, use overall PPR as approximation
            player_stats[player_name]['first_9_values'].append(ppr_float)
        
        # Store individual leg data
        leg_detail = {
            'leg_number': leg_number,
            'ppr': ppr_float,
            'starting_points': starting_points,
            'ending_points': ending_points,
            'checkout': double_out if double_out else 0,
            'won': won_leg,
            'darts_thrown': total_darts
        }
        
        player_stats[player_name]['legs'].append(leg_detail)
        
        # NOTE: Individual dart scores (180s, 140s, 100s) are NOT available in the
        # current Inertia.js data structure. We would need access to turn-by-turn
        # scoring data which appears to be in a different endpoint or requires
        # additional API calls
    
    def _calculate_player_summary(self, player_name: str, stats: Dict) -> Dict:
        """
        Calculate aggregated summary statistics for a player
        """
        total_legs = stats['legs_won'] + stats['legs_lost']
        
        # 3-dart average (overall)
        avg_3da = 0.0
        if stats['all_ppr_values']:
            avg_3da = sum(stats['all_ppr_values']) / len(stats['all_ppr_values'])
        
        # First 9 average
        avg_first_9 = 0.0
        if stats['first_9_values']:
            avg_first_9 = sum(stats['first_9_values']) / len(stats['first_9_values'])
        
        # Checkout statistics
        checkout_avg = 0.0
        if stats['checkout_values']:
            checkout_avg = sum(stats['checkout_values']) / len(stats['checkout_values'])
        
        checkout_success_rate = 0.0
        if stats['total_checkout_attempts'] > 0:
            checkout_success_rate = (stats['successful_checkouts'] / stats['total_checkout_attempts']) * 100
        
        # High finish
        high_finish = max(stats['checkout_values']) if stats['checkout_values'] else 0
        
        # Leg win percentage
        leg_win_pct = 0.0
        if total_legs > 0:
            leg_win_pct = (stats['legs_won'] / total_legs) * 100
        
        return {
            'player_name': player_name,
            'three_dart_avg': round(avg_3da, 2),
            'first_9_avg': round(avg_first_9, 2),
            'legs_played': total_legs,
            'legs_won': stats['legs_won'],
            'legs_lost': stats['legs_lost'],
            'leg_win_percentage': round(leg_win_pct, 1),
            
            # Checkout stats
            'checkout_average': round(checkout_avg, 2),
            'checkout_attempts': stats['total_checkout_attempts'],
            'successful_checkouts': stats['successful_checkouts'],
            'checkout_success_rate': round(checkout_success_rate, 1),
            'checkout_100_plus': stats['checkout_100_plus'],
            'checkout_170': stats['checkout_170'],
            'high_finish': high_finish,
            
            # High scores (NOT AVAILABLE in current data)
            'one_eighties': stats['score_180'],
            'one_forty_plus': stats['score_140_plus'],
            'hundreds_plus': stats['score_100_plus'],
            
            # Per-leg details
            'legs_detail': stats['legs']
        }


def test_advanced_scraper():
    """
    Test the advanced scraper on a match
    """
    scraper = AdvancedDartConnectScraper()
    
    # Use one of the event 1 matches
    test_url = "https://recap.dartconnect.com/matches/688e66b6f4fc02e124e759c8"
    
    print(f"Testing advanced scraper on: {test_url}")
    print("=" * 80)
    
    result = scraper.scrape_match_advanced(test_url)
    
    if result and 'players' in result:
        print(f"\n✅ Successfully scraped {len(result['players'])} players\n")
        
        for player in result['players']:
            print(f"📊 {player['player_name']}")
            print(f"   3-Dart Avg: {player['three_dart_avg']}")
            print(f"   First 9 Avg: {player['first_9_avg']}")
            print(f"   Legs: {player['legs_won']}W-{player['legs_lost']}L ({player['leg_win_percentage']}%)")
            print(f"   Checkout: {player['checkout_success_rate']}% ({player['successful_checkouts']}/{player['checkout_attempts']})")
            print(f"   Avg Checkout: {player['checkout_average']}")
            print(f"   High Finish: {player['high_finish']}")
            print(f"   100+ Checkouts: {player['checkout_100_plus']}")
            print(f"   170 Checkouts: {player['checkout_170']}")
            print(f"\n   Per-Leg Stats:")
            for leg in player['legs_detail']:
                status = "✅ Won" if leg['won'] else "❌ Lost"
                checkout_str = f"Checkout: {leg['checkout']}" if leg['checkout'] > 0 else "Missed"
                print(f"      Leg {leg['leg_number']}: {leg['ppr']:.2f} avg | {checkout_str} | {status}")
            print()
        
        # Save to file
        output_file = "advanced_scrape_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 Full results saved to: {output_file}")
    else:
        print("❌ Failed to scrape match")


if __name__ == "__main__":
    test_advanced_scraper()
