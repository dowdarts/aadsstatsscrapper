"""
DartConnect Match Recap Scraper
Extracts player statistics from DartConnect Match Recap pages
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DartConnectScraper:
    """
    Scrapes player statistics from DartConnect Match Recap pages.
    
    Features:
    - Extracts player names, averages, and scoring statistics
    - Handles various DartConnect page formats
    - Robust error handling for private/failed URLs
    - Rate limiting to avoid overwhelming the server
    """
    
    def __init__(self, rate_limit: float = 1.0):
        """
        Initialize the scraper.
        
        Args:
            rate_limit: Minimum seconds between requests (default: 1.0)
        """
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _rate_limit_wait(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def _validate_url(self, url: str) -> bool:
        """
        Validate that the URL is a DartConnect recap URL.
        
        Args:
            url: URL to validate
        
        Returns:
            True if valid DartConnect URL, False otherwise
        """
        try:
            parsed = urlparse(url)
            return 'dartconnect' in parsed.netloc.lower()
        except Exception:
            return False
    
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a DartConnect page.
        
        Args:
            url: URL to fetch
        
        Returns:
            BeautifulSoup object or None if failed
        """
        if not self._validate_url(url):
            logger.error(f"Invalid DartConnect URL: {url}")
            return None
        
        self._rate_limit_wait()
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Check if page is private or restricted
            if "private" in response.text.lower() or "not found" in response.text.lower():
                logger.warning(f"Page appears to be private or not found: {url}")
                return None
            
            return BeautifulSoup(response.text, 'html.parser')  # Using html.parser (built-in)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def _extract_number(self, text: str) -> float:
        """
        Extract a number from text, handling various formats.
        
        Args:
            text: Text containing a number
        
        Returns:
            Extracted number as float, or 0 if not found
        """
        if not text:
            return 0.0
        
        # Remove non-numeric characters except decimal point and minus
        cleaned = re.sub(r'[^\d.-]', '', str(text))
        
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0
    
    def scrape_match_recap(self, url: str) -> List[Dict]:
        """
        Scrape player statistics from a DartConnect Match Recap page.
        
        Args:
            url: DartConnect Match Recap URL
        
        Returns:
            List of player statistics dictionaries
        """
        logger.info(f"Scraping match recap: {url}")
        
        soup = self._fetch_page(url)
        if not soup:
            return []
        
        players_stats = []
        
        try:
            # Method 1: Look for standard stats table
            stats = self._parse_standard_table(soup)
            if stats:
                players_stats.extend(stats)
                logger.info(f"Extracted {len(stats)} player(s) using standard table method")
                return players_stats
            
            # Method 2: Look for alternative format (if standard fails)
            stats = self._parse_alternative_format(soup)
            if stats:
                players_stats.extend(stats)
                logger.info(f"Extracted {len(stats)} player(s) using alternative method")
                return players_stats
            
            logger.warning(f"No player statistics found on page: {url}")
        
        except Exception as e:
            logger.error(f"Error parsing page {url}: {e}", exc_info=True)
        
        return players_stats
    
    def _parse_standard_table(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parse statistics from standard DartConnect table format.
        
        Args:
            soup: BeautifulSoup object of the page
        
        Returns:
            List of player statistics dictionaries
        """
        players = []
        
        # Look for player statistics tables
        # DartConnect typically uses tables with class containing 'stats' or 'player'
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                # Try to identify player row by looking for player name and stats
                if len(cells) >= 6:  # Minimum cells for meaningful stats
                    player_data = self._extract_player_from_row(cells)
                    if player_data:
                        players.append(player_data)
        
        return players
    
    def _extract_player_from_row(self, cells: List) -> Optional[Dict]:
        """
        Extract player statistics from a table row.
        
        Args:
            cells: List of table cells (td/th elements)
        
        Returns:
            Player statistics dictionary or None
        """
        try:
            # This is a generic parser - adjust based on actual DartConnect format
            # Common DartConnect formats include:
            # [Player Name, 3DA, First 9, 100+, 140+, 180s, High Finish]
            
            # Skip header rows
            if cells[0].name == 'th':
                return None
            
            # Extract text from cells
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Look for player name (usually first cell or contains letters)
            player_name = None
            for text in cell_texts[:3]:  # Check first few cells
                if text and not text.replace('.', '').isdigit():
                    player_name = text
                    break
            
            if not player_name or len(player_name) < 2:
                return None
            
            # Extract numeric stats
            numbers = [self._extract_number(text) for text in cell_texts]
            
            # Filter out zeros and likely candidates for each stat
            potential_3da = [n for n in numbers if 40 <= n <= 120]  # 3DA range
            potential_180s = [n for n in numbers if 0 <= n <= 50]   # 180s count
            potential_high_finish = [n for n in numbers if 0 <= n <= 170]  # Checkout range
            
            # Build stats dictionary with defaults
            stats = {
                "player_name": player_name,
                "three_dart_avg": potential_3da[0] if potential_3da else 0.0,
                "legs_played": 5,  # Default, adjust if legs info is available
                "first_9_avg": potential_3da[1] if len(potential_3da) > 1 else (potential_3da[0] if potential_3da else 0.0),
                "hundreds_plus": int(numbers[3]) if len(numbers) > 3 else 0,
                "one_forty_plus": int(numbers[4]) if len(numbers) > 4 else 0,
                "one_eighties": int(numbers[5]) if len(numbers) > 5 else 0,
                "high_finish": int(potential_high_finish[-1]) if potential_high_finish else 0
            }
            
            # Validate that we have at least a reasonable 3DA
            if stats["three_dart_avg"] > 0:
                return stats
        
        except Exception as e:
            logger.debug(f"Error extracting player from row: {e}")
        
        return None
    
    def _parse_alternative_format(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parse DartConnect Recap pages that use Inertia.js with embedded JSON.
        The data is in a div#app with data-page attribute containing JSON.
        
        Args:
            soup: BeautifulSoup object of the page
        
        Returns:
            List of player statistics dictionaries
        """
        players = []
        
        try:
            # Find the app div with Inertia data
            app_div = soup.find('div', {'id': 'app'})
            if not app_div or not app_div.has_attr('data-page'):
                logger.warning("No Inertia.js data-page found, page may use different format")
                return players
            
            # Parse the JSON data (it's HTML-encoded)
            import html
            import json
            
            page_data_encoded = app_div['data-page']
            page_data = html.unescape(page_data_encoded)
            data = json.loads(page_data)
            
            if 'props' not in data:
                logger.error("No props in Inertia data")
                return players
            
            props = data['props']
            logger.debug(f"Found Inertia props with keys: {list(props.keys())}")
            
            # Get segments (contains leg-by-leg match data)
            # Structure: segments is a dict, typically with an empty string key ''
            # segments[''] = [[leg1_dict, leg2_dict, ...]]
            segments = props.get('segments', {})
            
            # Collect statistics per player
            player_stats = {}
            
            # Process each segment
            for segment_key, segment_list in segments.items():
                if not segment_list or len(segment_list) == 0:
                    continue
                
                # segment_list[0] contains the list of legs
                legs_list = segment_list[0]
                
                if not isinstance(legs_list, list):
                    continue
                
                # Process each leg
                for leg_data in legs_list:
                    if not isinstance(leg_data, dict):
                        continue
                    
                    # Process home player
                    if 'home' in leg_data:
                        home_data = leg_data['home']
                        # Get player name from players list
                        if 'players' in home_data and home_data['players']:
                            player_name = home_data['players'][0].get('player_label', '').strip()
                            
                            if player_name:
                                if player_name not in player_stats:
                                    player_stats[player_name] = {
                                        'legs_played': 0,
                                        'total_ppr': 0.0,
                                        'ppr_values': [],
                                        'high_finish': 0
                                    }
                                
                                # Add leg statistics
                                player_stats[player_name]['legs_played'] += 1
                                
                                # Get PPR (points per round) and convert to 3DA
                                ppr = home_data.get('ppr')
                                if ppr:
                                    try:
                                        ppr_float = float(ppr)
                                        player_stats[player_name]['ppr_values'].append(ppr_float)
                                        player_stats[player_name]['total_ppr'] += ppr_float
                                    except (ValueError, TypeError):
                                        pass
                                
                                # Track high finish (double_out_points)
                                finish = home_data.get('double_out_points', 0)
                                if finish and finish > player_stats[player_name]['high_finish']:
                                    player_stats[player_name]['high_finish'] = finish
                    
                    # Process away player
                    if 'away' in leg_data:
                        away_data = leg_data['away']
                        # Get player name from players list
                        if 'players' in away_data and away_data['players']:
                            player_name = away_data['players'][0].get('player_label', '').strip()
                            
                            if player_name:
                                if player_name not in player_stats:
                                    player_stats[player_name] = {
                                        'legs_played': 0,
                                        'total_ppr': 0.0,
                                        'ppr_values': [],
                                        'high_finish': 0
                                    }
                                
                                # Add leg statistics
                                player_stats[player_name]['legs_played'] += 1
                                
                                # Get PPR and convert to 3DA
                                ppr = away_data.get('ppr')
                                if ppr:
                                    try:
                                        ppr_float = float(ppr)
                                        player_stats[player_name]['ppr_values'].append(ppr_float)
                                        player_stats[player_name]['total_ppr'] += ppr_float
                                    except (ValueError, TypeError):
                                        pass
                                
                                # Track high finish
                                finish = away_data.get('double_out_points', 0)
                                if finish and finish > player_stats[player_name]['high_finish']:
                                    player_stats[player_name]['high_finish'] = finish
            
            # Convert to list format with calculated averages
            for player_name, stats in player_stats.items():
                # Calculate average PPR (which is basically the 3-dart average)
                if stats['ppr_values']:
                    avg_ppr = sum(stats['ppr_values']) / len(stats['ppr_values'])
                else:
                    avg_ppr = 0.0
                
                player_dict = {
                    "player_name": player_name,
                    "three_dart_avg": avg_ppr,  # PPR in DartConnect is essentially the 3DA
                    "legs_played": stats['legs_played'],
                    "first_9_avg": avg_ppr,  # Use same as 3DA for now
                    "hundreds_plus": 0,  # Not available in current data structure
                    "one_forty_plus": 0,  # Not available
                    "one_eighties": 0,  # Not available
                    "high_finish": stats['high_finish']
                }
                players.append(player_dict)
            
            logger.info(f"Parsed {len(players)} players from Inertia.js data")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON data from data-page: {e}")
        except Exception as e:
            logger.error(f"Error parsing alternative format: {e}", exc_info=True)
        
        return players
    
    def scrape_multiple_urls(self, urls: List[str], event_id: int = 1) -> Tuple[List[Dict], List[str]]:
        """
        Scrape multiple DartConnect URLs and aggregate results.
        
        Args:
            urls: List of DartConnect Match Recap URLs
            event_id: Event ID for these matches
        
        Returns:
            Tuple of (successful results, failed URLs)
        """
        all_stats = []
        failed_urls = []
        
        logger.info(f"Scraping {len(urls)} URLs for Event {event_id}")
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing URL {i}/{len(urls)}")
            
            stats = self.scrape_match_recap(url)
            
            if stats:
                # Add event_id to each player's stats
                for stat in stats:
                    stat['event_id'] = event_id
                all_stats.extend(stats)
            else:
                failed_urls.append(url)
        
        logger.info(f"Successfully scraped {len(all_stats)} player stats")
        if failed_urls:
            logger.warning(f"Failed to scrape {len(failed_urls)} URLs")
        
        return all_stats, failed_urls


# Example usage and testing
if __name__ == "__main__":
    scraper = DartConnectScraper()
    
    # Test with a URL (replace with actual DartConnect URL)
    test_url = "https://www.dartconnect.com/game/recap/EXAMPLE"
    
    # Note: This is a template. Actual DartConnect URLs needed for real testing
    print("DartConnect Scraper initialized.")
    print("To use: scraper.scrape_match_recap('YOUR_DARTCONNECT_URL')")
    print("\nExample:")
    print("  stats = scraper.scrape_match_recap(test_url)")
    print("  for player in stats:")
    print("      print(player)")
