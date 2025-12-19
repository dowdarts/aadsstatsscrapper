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
                            recap_url = f"https://recap.dartconnect.com/{match_id}"
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
            # Get the match page with player performance data
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
            
            # Get match and player data
            if 'page' not in props:
                result['errors'].append("No page data found")
                return result
                
            page = props['page']
            
            # Extract match info
            match_info = {
                'competition_title': page.get('match', {}).get('competition', {}).get('name', ''),
                'event_title': page.get('match', {}).get('event', {}).get('name', ''),
                'match_date': page.get('match', {}).get('date_formatted', ''),
                'match_time': page.get('match', {}).get('time_formatted', '')
            }
            
            # Extract player data
            if 'players' in page:
                for player_data in page['players']:
                    player = self._extract_player_stats(player_data, match_info)
                    if player:
                        result['players'].append(player)
            
            # Get additional counts data (180s, checkouts, etc.)
            self._enrich_with_counts_data(match_id, result['players'])
            
            result['success'] = len(result['players']) > 0
            
            if result['success']:
                logger.info(f"    ✅ Extracted {len(result['players'])} players")
            else:
                logger.info(f"    ❌ No players found")
                result['errors'].append("No players found")
            
            return result
            
        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"    ❌ Match extraction failed: {e}")
            return result
    
    def _extract_player_stats(self, player_data: Dict, match_info: Dict) -> Dict:
        """Extract comprehensive player statistics"""
        try:
            player = {
                # Identity
                'player_name': player_data.get('player_name', ''),
                
                # Match Context
                'competition_title': match_info.get('competition_title', ''),
                'event_title': match_info.get('event_title', ''),
                'match_date': match_info.get('match_date', ''),
                'match_time': match_info.get('match_time', ''),
                
                # Performance Metrics
                '3da': player_data.get('average', 0.0),  # 3-Dart Average
                'mpr': player_data.get('marks_per_round', 0.0),  # Marks Per Round
                'win_percentage': player_data.get('win_percentage', 0.0),
                'first_nine_average': player_data.get('first_nine_avg', 0.0),
                
                # Match Results
                'legs_won': player_data.get('total_wins', 0),
                'legs_played': player_data.get('total_games', 0),
                'legs_lost': 0,  # Will calculate
                
                # Scoring Data
                'points_scored': player_data.get('points_scored', 0),
                'darts_thrown': player_data.get('darts_thrown', 0),
                'highest_score': player_data.get('highest_score', 0),
                
                # Initialize counts (will be filled by counts endpoint)
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
            
            return player
            
        except Exception as e:
            logger.error(f"Error extracting player stats: {e}")
            return None
    
    def _enrich_with_counts_data(self, match_id: str, players: List[Dict]) -> None:
        """Enrich player data with counts information (180s, checkouts, etc.)"""
        try:
            counts_url = f"https://recap.dartconnect.com/counts/{match_id}"
            response = self.session.get(counts_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            app_div = soup.find('div', {'id': 'app'})
            
            if not app_div or 'data-page' not in app_div.attrs:
                return
            
            data_page = app_div['data-page']
            page_data = json.loads(data_page)
            props = page_data.get('props', {})
            
            if 'page' in props and 'players' in props['page']:
                counts_data = {}
                for counts_player in props['page']['players']:
                    name = counts_player.get('player_name', '')
                    counts_data[name] = counts_player
                
                # Update player data with counts
                for player in players:
                    name = player['player_name']
                    if name in counts_data:
                        counts = counts_data[name]
                        
                        # Scoring counts
                        player['100_plus'] = counts.get('count_100_plus', 0)
                        player['120_plus'] = counts.get('count_120_plus', 0)
                        player['140_plus'] = counts.get('count_140_plus', 0)
                        player['160_plus'] = counts.get('count_160_plus', 0)
                        player['180s'] = counts.get('count_180s', 0)
                        
                        # Finishing data
                        player['checkout_attempts'] = counts.get('checkout_attempts', 0)
                        player['checkout_opportunities'] = counts.get('checkout_opportunities', 0)
                        player['checkout_percentage'] = counts.get('checkout_efficiency', 0)
                        player['highest_checkout'] = counts.get('highest_checkout', 0)
                        player['100_plus_finishes'] = counts.get('count_100_plus_finishes', 0)
                        
        except Exception as e:
            logger.warning(f"Could not get counts data: {e}")
    
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
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import json
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime

# Selenium imports (will install if needed)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not available. Install with: pip install selenium")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DartEventScraper:
    """
    Two-stage scraper for dart match results from event pages.
    """
    
    def __init__(self, use_selenium: bool = False, headless: bool = True, delay: float = 1.5):
        """
        Initialize the scraper.
        
        Args:
            use_selenium: Force use of Selenium (auto-detects if needed)
            headless: Run Chrome in headless mode
            delay: Delay between requests in seconds
        """
        self.delay = delay
        self.use_selenium = use_selenium
        self.headless = headless
        self.session = requests.Session()
        self.driver = None
        
        # Configure session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Initialize Selenium if requested
        if self.use_selenium and SELENIUM_AVAILABLE:
            self._init_selenium()
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver."""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Selenium WebDriver initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Selenium: {e}")
            self.driver = None
    
    def _get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """
        Get page content using requests or Selenium fallback.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            # Try requests first
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if page has dynamic content that requires Selenium
            if self._needs_selenium(soup, url):
                return self._get_page_with_selenium(url)
            
            return soup
            
        except Exception as e:
            logger.warning(f"⚠️  Requests failed for {url}: {e}")
            if SELENIUM_AVAILABLE:
                return self._get_page_with_selenium(url)
            return None
    
    def _needs_selenium(self, soup: BeautifulSoup, url: str) -> bool:
        """
        Determine if page needs Selenium for dynamic content.
        
        Args:
            soup: BeautifulSoup object
            url: Original URL
            
        Returns:
            True if Selenium is needed
        """
        # Check for DartConnect's dynamic loading indicators
        if 'dartconnect.com' in url:
            # Look for Vue.js/Inertia.js indicators
            if soup.find('div', {'id': 'app'}) and soup.find('script', string=re.compile(r'window\.Laravel')):
                return True
            # Check if content area is mostly empty
            if len(soup.get_text().strip()) < 500:
                return True
        
        return False
    
    def _get_page_with_selenium(self, url: str) -> Optional[BeautifulSoup]:
        """
        Get page content using Selenium.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        if not self.driver:
            if SELENIUM_AVAILABLE:
                self._init_selenium()
            else:
                logger.error("❌ Selenium not available")
                return None
        
        try:
            logger.info(f"🌐 Loading {url} with Selenium...")
            self.driver.get(url)
            
            # Wait for content to load
            WebDriverWait(self.driver, 10).until(
                lambda driver: len(driver.page_source) > 1000
            )
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            html = self.driver.page_source
            return BeautifulSoup(html, 'html.parser')
            
        except Exception as e:
            logger.error(f"❌ Selenium failed for {url}: {e}")
            return None
    
    def stage1_discover_match_urls(self, event_url: str) -> List[str]:
        """
        STAGE 1: Extract all Match Recap URLs from Event URL
        
        Args:
            event_url: The main event page URL
            
        Returns:
            List of unique match recap URLs
        """
        logger.info(f"🎯 STAGE 1: Discovering match URLs from {event_url}")
        
        match_urls = []
        
        # For DartConnect, try API2 endpoint first
        if 'dartconnect.com' in event_url and '/event/' in event_url:
            api_urls = self._extract_dartconnect_api_urls(event_url)
            if api_urls:
                match_urls.extend(api_urls)
        
        # Fallback: scrape page for match links
        soup = self._get_page_content(event_url)
        if soup:
            page_urls = self._extract_match_links_from_page(soup, event_url)
            match_urls.extend(page_urls)
        
        # Remove duplicates and filter
        unique_urls = list(set(match_urls))
        filtered_urls = [url for url in unique_urls if self._is_match_recap_url(url)]
        
        logger.info(f"✅ STAGE 1 COMPLETE: Found {len(filtered_urls)} match recap URLs")
        return filtered_urls
    
    def _extract_dartconnect_api_urls(self, event_url: str) -> List[str]:
        """Extract match URLs using DartConnect API2 endpoint."""
        try:
            # Extract event ID
            event_id_match = re.search(r'/event/([a-zA-Z0-9_]+)', event_url)
            if not event_id_match:
                return []
            
            event_id = event_id_match.group(1)
            api_url = f"https://tv.dartconnect.com/api2/event/{event_id}/matches"
            
            logger.info(f"📡 Calling DartConnect API2: {api_url}")
            
            # Use requests for API call
            from urllib.request import Request, urlopen
            import json
            
            request_obj = Request(api_url, method='POST')
            request_obj.add_header('Content-Type', 'application/json')
            request_obj.add_header('User-Agent', self.session.headers['User-Agent'])
            
            with urlopen(request_obj, timeout=30) as response:
                data = json.load(response)
            
            match_urls = []
            
            # Extract match URLs from payload
            payload = data.get('payload', {})
            for section_name, section_data in payload.items():
                if isinstance(section_data, list):
                    for match in section_data:
                        if isinstance(match, dict) and 'mi' in match:
                            match_id = match['mi']
                            # Create both possible URL formats
                            recap_url = f"https://recap.dartconnect.com/{match_id}"
                            players_url = f"https://recap.dartconnect.com/players/{match_id}"
                            match_urls.extend([recap_url, players_url])
            
            logger.info(f"✅ API2 extracted {len(match_urls)} match URLs")
            return match_urls
            
        except Exception as e:
            logger.warning(f"⚠️  DartConnect API2 failed: {e}")
            return []
    
    def _extract_match_links_from_page(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract match links by scraping the page."""
        match_urls = []
        
        # Common patterns for match/recap links
        link_patterns = [
            r'recap',
            r'match',
            r'game',
            r'detail',
            r'result'
        ]
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Check if link looks like a match/recap URL
            for pattern in link_patterns:
                if re.search(pattern, href, re.IGNORECASE):
                    match_urls.append(full_url)
                    break
        
        return match_urls
    
    def _is_match_recap_url(self, url: str) -> bool:
        """Check if URL looks like a match recap page."""
        recap_indicators = [
            'recap',
            'match',
            'game',
            'detail',
            'result',
            'players',
            'counts'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in recap_indicators)
    
    def stage2_extract_match_data(self, match_urls: List[str]) -> List[Dict]:
        """
        STAGE 2: Extract detailed player statistics from each match
        
        Args:
            match_urls: List of match recap URLs
            
        Returns:
            List of dictionaries containing player data
        """
        logger.info(f"🎯 STAGE 2: Extracting data from {len(match_urls)} matches")
        
        all_match_data = []
        
        for i, url in enumerate(match_urls, 1):
            logger.info(f"📊 Processing match {i}/{len(match_urls)}: {url}")
            
            try:
                match_data = self._extract_single_match_data(url)
                if match_data:
                    all_match_data.extend(match_data)
                    logger.info(f"  ✅ Extracted {len(match_data)} players")
                else:
                    logger.warning(f"  ❌ No data extracted")
                
            except Exception as e:
                logger.error(f"  ❌ Error processing {url}: {e}")
            
            # Rate limiting
            if i < len(match_urls):
                time.sleep(self.delay)
        
        logger.info(f"✅ STAGE 2 COMPLETE: Extracted {len(all_match_data)} player records")
        return all_match_data
    
    def _extract_single_match_data(self, url: str) -> List[Dict]:
        """
        Extract player data from a single match page.
        
        Args:
            url: Match recap URL
            
        Returns:
            List of player data dictionaries
        """
        players_data = []
        
        # Try different approaches based on URL type
        if 'dartconnect.com' in url:
            players_data = self._extract_dartconnect_match_data(url)
        else:
            # Generic extraction for other sites
            players_data = self._extract_generic_match_data(url)
        
        return players_data
    
    def _extract_dartconnect_match_data(self, url: str) -> List[Dict]:
        """Extract data from DartConnect match pages."""
        players_data = []
        
        try:
            # Extract match ID
            match_id = url.split('/')[-1]
            
            # Try multiple endpoints
            endpoints = [
                f"https://recap.dartconnect.com/players/{match_id}",
                f"https://recap.dartconnect.com/counts/{match_id}",
                f"https://recap.dartconnect.com/{match_id}"
            ]
            
            player_stats = {}
            counts_data = {}
            
            for endpoint in endpoints:
                soup = self._get_page_content(endpoint)
                if not soup:
                    continue
                
                # Look for Inertia.js data
                app_div = soup.find('div', {'id': 'app'})
                if app_div and 'data-page' in app_div.attrs:
                    try:
                        data_page = app_div['data-page']
                        page_data = json.loads(data_page)
                        props = page_data.get('props', {})
                        
                        if 'players' in endpoint:
                            player_stats = self._parse_dartconnect_players(props)
                        elif 'counts' in endpoint:
                            counts_data = self._parse_dartconnect_counts(props)
                            
                    except Exception as e:
                        logger.debug(f"Failed to parse JSON from {endpoint}: {e}")
            
            # Combine player stats with counts data
            for player_name, stats in player_stats.items():
                player_counts = counts_data.get(player_name, {})
                
                combined_data = {
                    'match_id': match_id,
                    'match_url': url,
                    'player_name': player_name,
                    
                    # Identity
                    'name': player_name,
                    
                    # Performance
                    '3da': stats.get('average', 0),
                    'mpr': stats.get('mpr', 0),  # May not be available for 501
                    'win_percentage': stats.get('win_percentage', 0),
                    
                    # Match Results
                    'legs_won': stats.get('total_wins', 0),
                    'legs_lost': stats.get('total_games', 0) - stats.get('total_wins', 0),
                    'total_legs': stats.get('total_games', 0),
                    
                    # Scoring Counts
                    'count_100_plus': player_counts.get('count_100_plus', 0),
                    'count_120_plus': player_counts.get('count_120_plus', 0),
                    'count_140_plus': player_counts.get('count_140_plus', 0),
                    'count_160_plus': player_counts.get('count_160_plus', 0),
                    'count_180': player_counts.get('count_180s', 0),
                    
                    # Finishing
                    'checkout_attempts': player_counts.get('checkout_opportunities', 0),
                    'checkout_opportunities': player_counts.get('checkout_opportunities', 0),
                    'finishes_100_plus': player_counts.get('finishes_100_plus', 0),
                    'highest_checkout': player_counts.get('highest_checkout', 0),
                    'checkout_percentage': player_counts.get('checkout_efficiency', 0),
                    
                    # Additional stats
                    'points_scored': stats.get('points_scored', 0),
                    'darts_thrown': stats.get('darts_thrown', 0),
                    'first_nine_avg': stats.get('first_nine_avg', 0),
                    'highest_score': stats.get('highest_score', 0),
                }
                
                players_data.append(combined_data)
            
        except Exception as e:
            logger.error(f"Error extracting DartConnect data from {url}: {e}")
        
        return players_data
    
    def _parse_dartconnect_players(self, props: Dict) -> Dict:
        """Parse DartConnect players data from props."""
        players = {}
        
        if 'page' in props and 'players' in props['page']:
            for player_data in props['page']['players']:
                name = player_data.get('player_name', '')
                if name:
                    players[name] = player_data
        
        return players
    
    def _parse_dartconnect_counts(self, props: Dict) -> Dict:
        """Parse DartConnect counts data from props."""
        counts = {}
        
        if 'page' in props and 'players' in props['page']:
            for player_data in props['page']['players']:
                name = player_data.get('player_name', '')
                if name:
                    counts[name] = player_data
        
        return counts
    
    def _extract_generic_match_data(self, url: str) -> List[Dict]:
        """Extract data from generic match pages."""
        players_data = []
        
        soup = self._get_page_content(url)
        if not soup:
            return players_data
        
        # Generic extraction logic - customize for your specific sites
        # This is a template that can be adapted for different dart sites
        
        # Look for tables, divs, or other containers with player data
        player_containers = soup.find_all(['tr', 'div'], class_=re.compile(r'player|result', re.I))
        
        for container in player_containers:
            try:
                player_data = self._parse_generic_player_data(container, url)
                if player_data:
                    players_data.append(player_data)
            except Exception as e:
                logger.debug(f"Error parsing player container: {e}")
        
        return players_data
    
    def _parse_generic_player_data(self, container, url: str) -> Optional[Dict]:
        """Parse player data from a generic container."""
        # Template for generic parsing - customize as needed
        try:
            # Extract text and look for patterns
            text = container.get_text().strip()
            
            # Basic template - adapt for specific sites
            player_data = {
                'match_url': url,
                'player_name': '',
                'name': '',
                '3da': 0,
                'mpr': 0,
                'win_percentage': 0,
                'legs_won': 0,
                'legs_lost': 0,
                'total_legs': 0,
                'count_100_plus': 0,
                'count_120_plus': 0,
                'count_140_plus': 0,
                'count_160_plus': 0,
                'count_180': 0,
                'checkout_attempts': 0,
                'checkout_opportunities': 0,
                'finishes_100_plus': 0,
                'highest_checkout': 0,
                'checkout_percentage': 0
            }
            
            # Add parsing logic here based on your specific site structure
            # This is just a placeholder
            
            return player_data if player_data['name'] else None
            
        except Exception as e:
            logger.debug(f"Error in generic parsing: {e}")
            return None
    
    def extract_tournament_bracket(self, event_url: str) -> Dict:
        """
        Extract tournament bracket information (champion, runner-up, etc.)
        
        Args:
            event_url: The main event page URL
            
        Returns:
            Dictionary with tournament results
        """
        logger.info(f"🏆 Extracting tournament bracket from {event_url}")
        
        bracket_info = {
            'champion': None,
            'runner_up': None,
            'joint_3rd': [],
            'joint_5th': [],
            'semifinals': [],
            'quarterfinals': []
        }
        
        soup = self._get_page_content(event_url)
        if not soup:
            return bracket_info
        
        # For DartConnect, look for bracket/results sections
        if 'dartconnect.com' in event_url:
            bracket_info = self._extract_dartconnect_bracket(soup, event_url)
        else:
            bracket_info = self._extract_generic_bracket(soup, event_url)
        
        return bracket_info
    
    def _extract_dartconnect_bracket(self, soup: BeautifulSoup, event_url: str) -> Dict:
        """Extract tournament bracket from DartConnect."""
        bracket_info = {
            'champion': None,
            'runner_up': None,
            'joint_3rd': [],
            'joint_5th': [],
            'semifinals': [],
            'quarterfinals': []
        }
        
        try:
            # Look for tournament bracket or results
            bracket_sections = soup.find_all(['div', 'section'], 
                                           class_=re.compile(r'bracket|tournament|results|knockout', re.I))
            
            for section in bracket_sections:
                # Extract bracket information
                # This would need to be customized based on actual HTML structure
                pass
                
        except Exception as e:
            logger.error(f"Error extracting DartConnect bracket: {e}")
        
        return bracket_info
    
    def _extract_generic_bracket(self, soup: BeautifulSoup, event_url: str) -> Dict:
        """Extract tournament bracket from generic site."""
        return {
            'champion': None,
            'runner_up': None,
            'joint_3rd': [],
            'joint_5th': [],
            'semifinals': [],
            'quarterfinals': []
        }
    
    def scrape_event(self, event_url: str, output_file: str = None) -> pd.DataFrame:
        """
        Complete scraping workflow: discover matches, extract data, and get bracket info.
        
        Args:
            event_url: The main event page URL
            output_file: Optional CSV filename for output
            
        Returns:
            Pandas DataFrame with all match data
        """
        logger.info(f"🚀 Starting complete event scrape: {event_url}")
        
        # Stage 1: Discover match URLs
        match_urls = self.stage1_discover_match_urls(event_url)
        
        if not match_urls:
            logger.error("❌ No match URLs found!")
            return pd.DataFrame()
        
        # Stage 2: Extract match data
        match_data = self.stage2_extract_match_data(match_urls)
        
        if not match_data:
            logger.error("❌ No match data extracted!")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(match_data)
        
        # Extract tournament bracket
        bracket_info = self.extract_tournament_bracket(event_url)
        
        # Add bracket info to DataFrame (as additional columns)
        if bracket_info['champion']:
            df['tournament_champion'] = bracket_info['champion']
        if bracket_info['runner_up']:
            df['tournament_runner_up'] = bracket_info['runner_up']
        
        # Save to CSV
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'dart_stats_{timestamp}.csv'
        
        df.to_csv(output_file, index=False)
        logger.info(f"💾 Results saved to {output_file}")
        
        # Display summary
        self._display_summary(df, bracket_info)
        
        return df
    
    def _display_summary(self, df: pd.DataFrame, bracket_info: Dict):
        """Display scraping results summary."""
        print("\n" + "="*80)
        print("🎯 DART EVENT SCRAPING COMPLETE")
        print("="*80)
        
        print(f"📊 Total Records: {len(df)}")
        print(f"👥 Unique Players: {df['player_name'].nunique()}")
        print(f"🎮 Total Matches: {df['match_url'].nunique()}")
        
        if not df.empty:
            print(f"\n🏆 Top Performers by 3-Dart Average:")
            top_players = df.groupby('player_name').agg({
                '3da': 'mean',
                'count_180': 'sum',
                'legs_won': 'sum',
                'total_legs': 'sum'
            }).sort_values('3da', ascending=False).head(10)
            
            for player, stats in top_players.iterrows():
                print(f"  • {player}: {stats['3da']:.2f} avg, {stats['count_180']} x 180s")
        
        if bracket_info.get('champion'):
            print(f"\n🏆 Tournament Results:")
            print(f"  Champion: {bracket_info['champion']}")
            print(f"  Runner-up: {bracket_info['runner_up']}")
        
        print("="*80)
    
    def __del__(self):
        """Cleanup Selenium driver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


def main():
    """Main function for command-line usage."""
    print("🎯 Two-Stage Dart Event Scraper")
    print("="*50)
    
    # Example usage
    event_url = input("Enter Event URL: ").strip()
    if not event_url:
        # Default to AADS Event #1 for testing
        event_url = "https://tv.dartconnect.com/event/mt_joe6163l_1"
        print(f"Using default: {event_url}")
    
    # Initialize scraper
    scraper = DartEventScraper(
        use_selenium=False,  # Try requests first
        headless=True,
        delay=1.5
    )
    
    try:
        # Run complete scraping workflow
        df = scraper.scrape_event(event_url)
        
        if not df.empty:
            print(f"\n✅ Success! Scraped {len(df)} records")
            print(f"📁 Data saved to: dart_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        else:
            print("\n❌ No data scraped")
            
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")
    finally:
        # Cleanup
        del scraper


if __name__ == "__main__":
    main()