#!/usr/bin/env python3
"""
Two-Stage Dart Match Scraper for DartConnect
Meets exact specifications from prompt including CSV export and tournament bracket

Stage 1: Discovery - Find all match recap URLs from event page
Stage 2: Data Extraction - Extract comprehensive player stats from each match
Final: Export to Pandas DataFrame and save as dart_stats.csv

Author: Expert Python Developer specializing in web scraping
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TwoStageDartScraper:
    """
    Two-stage web scraper for dart match results from DartConnect events.
    
    Uses requests and BeautifulSoup with error handling and rate limiting.
    """
    
    def __init__(self, delay: float = 1.5):
        """Initialize scraper with rate limiting"""
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def stage1_discovery(self, event_url: str) -> List[str]:
        """
        Stage 1: Discovery
        Navigate to event page and find all match recap URLs.
        
        Args:
            event_url: DartConnect event URL
            
        Returns:
            List of unique match recap URLs
        """
        logger.info(f"🎯 STAGE 1: Discovery - {event_url}")
        
        try:
            # Extract event ID from URL
            event_id_match = re.search(r'/event/([a-zA-Z0-9_]+)', event_url)
            if not event_id_match:
                raise ValueError("Could not extract event ID from URL")
            
            event_id = event_id_match.group(1)
            logger.info(f"📋 Event ID: {event_id}")
            
            # Use DartConnect API2 for reliable match discovery
            api_url = f"https://tv.dartconnect.com/api2/event/{event_id}/matches"
            logger.info(f"🔗 Calling API: {api_url}")
            
            response = self.session.post(api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ API response received")
            
            # Extract match URLs from response
            match_urls = []
            payload = data.get('payload', {})
            
            # Check both 'completed' and 'events' sections
            for section_name in ['completed', 'events']:
                if section_name in payload and isinstance(payload[section_name], list):
                    for match in payload[section_name]:
                        if isinstance(match, dict) and 'id' in match:
                            match_id = match['id']
                            # Use players endpoint for extraction
                            recap_url = f"https://recap.dartconnect.com/players/{match_id}"
                            match_urls.append(recap_url)
                            logger.info(f"  📄 Found match: {match_id}")
            
            logger.info(f"✅ STAGE 1 COMPLETE: Found {len(match_urls)} match URLs")
            return match_urls
            
        except Exception as e:
            logger.error(f"❌ Stage 1 failed: {e}")
            raise
    
    def stage2_extract_match_data(self, match_url: str) -> Dict:
        """
        Stage 2: Data Extraction
        Extract comprehensive player data from a single match recap page.
        
        Args:
            match_url: URL to match recap page
            
        Returns:
            Dictionary with extracted player data
        """
        match_id = match_url.split('/')[-1]
        
        result = {
            'match_id': match_id,
            'match_url': match_url,
            'players': [],
            'success': False,
            'errors': []
        }
        
        try:
            # Get basic player data from players endpoint
            players_url = f"https://recap.dartconnect.com/players/{match_id}"
            response = self.session.get(players_url, timeout=15)
            response.raise_for_status()
            
            # Parse HTML and extract JSON data from Inertia.js
            soup = BeautifulSoup(response.text, 'html.parser')
            app_div = soup.find('div', {'id': 'app'})
            
            if not app_div or 'data-page' not in app_div.attrs:
                result['errors'].append("No Inertia.js data found")
                return result
            
            # Extract embedded JSON data
            data_page = app_div['data-page']
            page_data = json.loads(data_page)
            props = page_data.get('props', {})
            
            # Get match info from matchInfo
            match_info = props.get('matchInfo', {})
            match_details = {
                'competition_title': match_info.get('competition', {}).get('name', ''),
                'event_title': match_info.get('event', {}).get('name', ''),
                'match_date': match_info.get('date_formatted', ''),
                'match_time': match_info.get('time_formatted', '')
            }
            
            # Get basic player data
            players_data = props.get('players', [])
            
            # Get detailed performance data from counts endpoint
            counts_url = f"https://recap.dartconnect.com/counts/{match_id}"
            counts_response = self.session.get(counts_url, timeout=15)
            counts_response.raise_for_status()
            
            counts_soup = BeautifulSoup(counts_response.text, 'html.parser')
            counts_app_div = counts_soup.find('div', {'id': 'app'})
            
            if counts_app_div and 'data-page' in counts_app_div.attrs:
                counts_data_page = counts_app_div['data-page']
                counts_page_data = json.loads(counts_data_page)
                counts_props = counts_page_data.get('props', {})
                
                player_performances = counts_props.get('playerPerformances', [])
            else:
                player_performances = []
                result['errors'].append("Could not get counts data")
            
            # Merge basic and performance data
            for basic_player in players_data:
                player = self._extract_player_stats(basic_player, match_details, player_performances)
                if player:
                    result['players'].append(player)
            
            result['success'] = len(result['players']) > 0
            
            if result['success']:
                logger.info(f"    ✅ Extracted {len(result['players'])} players with detailed stats")
            else:
                logger.info(f"    ❌ No players found")
                result['errors'].append("No players found")
            
            return result
            
        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"    ❌ Match extraction failed: {e}")
            return result
    
    def _extract_player_stats(self, basic_player: Dict, match_info: Dict, player_performances: List[Dict]) -> Dict:
        """Extract comprehensive player statistics from basic and performance data"""
        try:
            player_name = basic_player.get('name', '').strip()
            
            # Find matching performance data by name
            performance_data = None
            for perf in player_performances:
                if perf.get('name', '').strip().lower() == player_name.lower():
                    performance_data = perf
                    break
            
            # Basic player data
            player = {
                # Identity
                'player_name': player_name,
                
                # Match Context
                'competition_title': match_info.get('competition_title', ''),
                'event_title': match_info.get('event_title', ''),
                'match_date': match_info.get('match_date', ''),
                'match_time': match_info.get('match_time', ''),
                
                # Performance Metrics from basic data
                '3da': float(basic_player.get('average_01', '0').replace(',', '')),  # 3-Dart Average
                'mpr': 0.0,  # Not available in this format
                'win_percentage': float(basic_player.get('win_percentage', 0)),
                'first_nine_average': 0.0,  # Will be filled from performance data
                
                # Match Results
                'legs_won': int(basic_player.get('total_wins', 0)),
                'legs_played': int(basic_player.get('total_games', 0)),
                'legs_lost': 0,  # Will calculate
                
                # Scoring Data
                'points_scored': int(basic_player.get('points_scored_01', '0').replace(',', '')),
                'darts_thrown': int(basic_player.get('darts_thrown_01', '0').replace(',', '')),
                'highest_score': 0,  # Will be filled from performance data
                
                # Initialize scoring counts
                '100_plus': 0,
                '120_plus': 0,
                '140_plus': 0,
                '160_plus': 0,
                '180s': 0,
                
                # Finishing Data
                'checkout_attempts': 0,
                'checkout_opportunities': 0,
                'checkout_percentage': 0,
                'highest_checkout': 0,
                '100_plus_finishes': 0,
            }
            
            # Calculate legs lost
            if player['legs_played'] > 0:
                player['legs_lost'] = player['legs_played'] - player['legs_won']
            
            # Add performance data if available
            if performance_data:
                # First nine average
                player['first_nine_average'] = float(performance_data.get('first_nine', 0))
                
                # Checkout data
                checkout_eff = performance_data.get('coe', '0%').replace('%', '')
                try:
                    player['checkout_percentage'] = float(checkout_eff)
                except:
                    player['checkout_percentage'] = 0
                
                # Double out stats
                double_out_stats = performance_data.get('double_out_stats', {})
                if double_out_stats and double_out_stats.get('highest'):
                    player['highest_checkout'] = int(double_out_stats['highest'])
                
                if double_out_stats and double_out_stats.get('100_139'):
                    player['100_plus_finishes'] = int(double_out_stats['100_139'])
                
                # Distribution data (scoring counts)
                dist = performance_data.get('dist', {})
                plus_100 = dist.get('plus_100', {})
                
                if plus_100:
                    # Highest score
                    if plus_100.get('highest'):
                        player['highest_score'] = int(plus_100['highest'])
                    
                    # Scoring breakdowns
                    player['100_plus'] = int(plus_100.get('count', 0))
                    
                    # Extract specific ranges
                    count_120_139 = plus_100.get('120_139', 0)
                    count_140_159 = plus_100.get('140_159', 0)
                    count_160_179 = plus_100.get('160_179', 0)
                    count_180 = plus_100.get('180', 0)
                    
                    # Handle '-' values (means 0)
                    def safe_int(value):
                        return 0 if value == '-' else int(value)
                    
                    player['120_plus'] = safe_int(count_120_139) + safe_int(count_140_159) + safe_int(count_160_179) + safe_int(count_180)
                    player['140_plus'] = safe_int(count_140_159) + safe_int(count_160_179) + safe_int(count_180)
                    player['160_plus'] = safe_int(count_160_179) + safe_int(count_180)
                    player['180s'] = safe_int(count_180)
            
            return player
            
        except Exception as e:
            logger.error(f"Error extracting player stats: {e}")
            return None
    
    def extract_tournament_bracket(self, event_url: str) -> Dict:
        """
        Extract tournament bracket information including champion, runner-up, etc.
        
        Args:
            event_url: DartConnect event URL
            
        Returns:
            Dictionary with tournament results
        """
        logger.info(f"🏆 Extracting tournament bracket from: {event_url}")
        
        bracket_info = {
            'champion': None,
            'runner_up': None,
            'joint_3rd': [],
            'joint_5th': [],
            'tournament_format': None,
            'total_players': 0
        }
        
        try:
            response = self.session.get(event_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            app_div = soup.find('div', {'id': 'app'})
            
            if app_div and 'data-page' in app_div.attrs:
                data_page = app_div['data-page']
                page_data = json.loads(data_page)
                props = page_data.get('props', {})
                
                # Extract tournament info
                if 'tournamentInfo' in props:
                    tournament_info = props['tournamentInfo']
                    bracket_info['tournament_format'] = tournament_info.get('format', 'Unknown')
                    bracket_info['total_players'] = len(tournament_info.get('players', []))
                
                # Extract tournament events (bracket structure)
                if 'tournamentEvents' in props:
                    events = props['tournamentEvents']
                    self._parse_bracket_results(events, bracket_info)
            
            logger.info(f"✅ Tournament bracket extracted")
            return bracket_info
            
        except Exception as e:
            logger.error(f"❌ Bracket extraction failed: {e}")
            return bracket_info
    
    def _parse_bracket_results(self, events: List[Dict], bracket_info: Dict) -> None:
        """Parse tournament events to determine final standings"""
        try:
            # Look for final and semi-final matches
            finals = []
            semi_finals = []
            
            for event in events:
                event_name = event.get('name', '').lower()
                matches = event.get('matches', [])
                
                if 'final' in event_name and 'semi' not in event_name:
                    finals.extend(matches)
                elif 'semi' in event_name:
                    semi_finals.extend(matches)
            
            # Determine champion and runner-up from finals
            if finals:
                for match in finals:
                    players = match.get('players', [])
                    if len(players) >= 2:
                        # Assuming winner is determined by score or status
                        winner, loser = self._determine_match_winner(match)
                        if winner:
                            bracket_info['champion'] = winner
                            bracket_info['runner_up'] = loser
            
            # Determine joint 3rd from semi-finals
            if semi_finals:
                semi_losers = []
                for match in semi_finals:
                    winner, loser = self._determine_match_winner(match)
                    if loser:
                        semi_losers.append(loser)
                bracket_info['joint_3rd'] = semi_losers
                
        except Exception as e:
            logger.error(f"Error parsing bracket: {e}")
    
    def _determine_match_winner(self, match: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Determine winner and loser from match data"""
        try:
            players = match.get('players', [])
            if len(players) < 2:
                return None, None
            
            # Sort by score or win status
            sorted_players = sorted(players, key=lambda p: p.get('score', 0), reverse=True)
            
            winner = sorted_players[0].get('name')
            loser = sorted_players[1].get('name')
            
            return winner, loser
            
        except Exception as e:
            logger.error(f"Error determining winner: {e}")
            return None, None
    
    def run_full_scrape(self, event_url: str) -> pd.DataFrame:
        """
        Run complete two-stage scraping process and return DataFrame.
        
        Args:
            event_url: DartConnect event URL
            
        Returns:
            Pandas DataFrame with all player statistics
        """
        logger.info(f"🚀 STARTING TWO-STAGE DART SCRAPER")
        logger.info(f"📍 Event URL: {event_url}")
        logger.info("=" * 80)
        
        all_player_data = []
        
        try:
            # Stage 1: Discovery
            match_urls = self.stage1_discovery(event_url)
            
            if not match_urls:
                logger.error("❌ No match URLs found")
                return pd.DataFrame()
            
            # Stage 2: Data Extraction
            logger.info(f"🎯 STAGE 2: Data Extraction - {len(match_urls)} matches")
            
            successful = 0
            failed = 0
            
            for i, match_url in enumerate(match_urls, 1):
                logger.info(f"🔄 Processing match {i}/{len(match_urls)}")
                
                # Extract match data
                match_result = self.stage2_extract_match_data(match_url)
                
                if match_result['success']:
                    successful += 1
                    all_player_data.extend(match_result['players'])
                else:
                    failed += 1
                    logger.warning(f"    ⚠️ Failed: {match_result['errors']}")
                
                # Rate limiting delay
                if i < len(match_urls):
                    time.sleep(self.delay)
            
            # Extract tournament bracket
            logger.info(f"🏆 STAGE 3: Tournament Bracket Extraction")
            bracket_results = self.extract_tournament_bracket(event_url)
            
            # Create DataFrame
            if all_player_data:
                df = pd.DataFrame(all_player_data)
                
                # Add tournament results as metadata
                df.attrs['tournament_results'] = bracket_results
                
                logger.info(f"✅ SUCCESS!")
                logger.info(f"📊 Matches processed: {successful}/{len(match_urls)}")
                logger.info(f"👥 Total player records: {len(all_player_data)}")
                logger.info(f"🏆 Champion: {bracket_results.get('champion', 'Unknown')}")
                logger.info("=" * 80)
                
                return df
            else:
                logger.error("❌ No player data extracted")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Full scrape failed: {e}")
            return pd.DataFrame()
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = "dart_stats.csv") -> bool:
        """
        Save DataFrame to CSV file.
        
        Args:
            df: DataFrame to save
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if df.empty:
                logger.error("❌ No data to save")
                return False
            
            # Save main data
            df.to_csv(filename, index=False)
            logger.info(f"💾 Data saved to: {filename}")
            
            # Save tournament results separately if available
            if hasattr(df, 'attrs') and 'tournament_results' in df.attrs:
                bracket_filename = filename.replace('.csv', '_tournament_results.json')
                with open(bracket_filename, 'w') as f:
                    json.dump(df.attrs['tournament_results'], f, indent=2)
                logger.info(f"🏆 Tournament results saved to: {bracket_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Save failed: {e}")
            return False


def main():
    """Main function demonstrating the scraper usage"""
    
    # Example usage
    event_url = "https://tv.dartconnect.com/event/mt_joe6163l_1"
    
    # Create scraper instance
    scraper = TwoStageDartScraper(delay=1.5)  # 1.5 second delay between requests
    
    # Run full scrape
    df = scraper.run_full_scrape(event_url)
    
    if not df.empty:
        # Display summary
        print("\n📊 SCRAPING RESULTS SUMMARY")
        print("=" * 50)
        print(f"Total records: {len(df)}")
        print(f"Unique players: {df['player_name'].nunique()}")
        print(f"Competitions: {df['competition_title'].nunique()}")
        
        # Show top performers
        print("\n🏆 TOP PERFORMERS (by 3DA):")
        top_players = df.groupby('player_name')['3da'].mean().sort_values(ascending=False).head(5)
        for i, (player, avg) in enumerate(top_players.items(), 1):
            print(f"{i}. {player}: {avg:.2f} average")
        
        # Save to CSV
        scraper.save_to_csv(df, "dart_stats.csv")
        
        print(f"\n✅ Complete! Results saved to 'dart_stats.csv'")
        
    else:
        print("❌ No data scraped")


if __name__ == "__main__":
    main()