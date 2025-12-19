"""
Background scraper with real-time progress tracking
"""
import json
import time
import re
import logging
from urllib.request import Request, urlopen
from scraper_comprehensive import scrape_match_comprehensive
from supabase import create_client
from datetime import datetime

logger = logging.getLogger(__name__)

def run_scrape_with_progress(job_id, event_url, event_name, progress_dict):
    """
    Background scraping job with progress updates.
    
    Args:
        job_id: Unique identifier for this scrape job
        event_url: DartConnect event URL
        event_name: Name of the event
        progress_dict: Shared dictionary for progress tracking
    """
    try:
        # Supabase config
        SUPABASE_URL = "https://kswwbqumgsdissnwuiab.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtzd3dicXVtZ3NkaXNzbnd1aWFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ0ODMwNTIsImV4cCI6MjA4MDA1OTA1Mn0.b-z8JqL1dBYJcrrzSt7u6VAaFAtTOl1vqqtFFgHkJ50"
        USER_ID = "116cc929-d60f-4ae4-ac53-b228b91ea8b3"
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Update progress: extracting URLs
        progress_dict[job_id]["status"] = "extracting_urls"
        progress_dict[job_id]["message"] = "Extracting match URLs from event page..."
        
        # ========================================================================
        # PART 1: EXTRACT MATCH URLs USING API2
        # ========================================================================
        logger.info(f"[{job_id}] Extracting match URLs from: {event_url}")
        
        # Extract event ID from URL
        event_id_match = re.search(r'/event/([a-zA-Z0-9_]+)', event_url)
        if not event_id_match:
            progress_dict[job_id]["status"] = "error"
            progress_dict[job_id]["message"] = "Could not extract event ID from URL"
            return
        
        extracted_event_id = event_id_match.group(1)
        
        # Call DartConnect API2
        api_url = f"https://tv.dartconnect.com/api2/event/{extracted_event_id}/matches"
        request_obj = Request(api_url, method='POST')
        request_obj.add_header('Content-Type', 'application/json')
        request_obj.add_header('User-Agent', 'Mozilla/5.0')
        
        try:
            with urlopen(request_obj, timeout=30) as response:
                result = json.loads(response.read().decode())
        except Exception as e:
            logger.error(f"[{job_id}] Failed to call API2: {e}")
            progress_dict[job_id]["status"] = "error"
            progress_dict[job_id]["message"] = f"Failed to extract matches: {str(e)}"
            progress_dict[job_id]["errors"].append(str(e))
            return
        
        # Extract match URLs from API2 payload
        match_urls = []
        payload = result.get('payload', {})
        
        for section_name, section_data in payload.items():
            if isinstance(section_data, list):
                for match in section_data:
                    if isinstance(match, dict) and 'mi' in match:
                        match_id = match['mi']
                        match_urls.append(f"https://recap.dartconnect.com/matches/{match_id}")
        
        if not match_urls:
            progress_dict[job_id]["status"] = "error"
            progress_dict[job_id]["message"] = "No match URLs found in event"
            return
        
        logger.info(f"[{job_id}] Found {len(match_urls)} match URLs")
        
        # Update progress with total
        progress_dict[job_id]["total_matches"] = len(match_urls)
        progress_dict[job_id]["status"] = "scraping"
        progress_dict[job_id]["message"] = f"Found {len(match_urls)} matches. Starting scrape..."
        
        # ========================================================================
        # PART 2: SCRAPE COMPREHENSIVE STATS FROM MATCH TABS
        # ========================================================================
        logger.info(f"[{job_id}] Scraping {len(match_urls)} matches with comprehensive stats")
        
        results = {
            "total_matches": len(match_urls),
            "successful": 0,
            "failed": 0,
            "players": {},
            "errors": []
        }
        
        DELAY_BETWEEN_MATCHES = 2.0
        MAX_RETRIES = 3
        
        def to_float(value, default=0.0):
            if value is None or value == '-' or value == '':
                return None if default is None else default
            try:
                return float(value)
            except (ValueError, TypeError):
                return None if default is None else default
        
        for i, url in enumerate(match_urls, 1):
            # Update progress
            match_id_short = url.split('/')[-1][:8]
            progress_dict[job_id]["current_match"] = i
            progress_dict[job_id]["current_match_name"] = match_id_short
            progress_dict[job_id]["progress"] = int((i / len(match_urls)) * 100)
            progress_dict[job_id]["message"] = f"Scraping match {i} of {len(match_urls)} ({match_id_short})..."
            
            logger.info(f"[{job_id}] Match {i}/{len(match_urls)}")
            
            # Extract match ID
            match_id_match = re.search(r'/matches/([a-f0-9]+)', url)
            if not match_id_match:
                results["failed"] += 1
                results["errors"].append(f"Invalid URL: {url}")
                progress_dict[job_id]["failed"] += 1
                continue
            
            match_id = match_id_match.group(1)
            
            # Retry logic
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    match_data = scrape_match_comprehensive(match_id)
                    
                    if match_data.get('players'):
                        # Upload each player's match stats
                        for player in match_data['players']:
                            # Clean data
                            points = player.get('points_scored', '0')
                            if isinstance(points, str):
                                points = points.replace(',', '')
                            
                            # Build complete record
                            record = {
                                'user_id': USER_ID,
                                'name': player.get('name'),
                                'event_name': event_name,
                                'match_id': match_id,
                                'legs_played': player.get('total_games', 0),
                                'legs_won': player.get('total_wins', 0),
                                'win_percentage': player.get('win_percentage', 0),
                                'total_darts': int(player.get('darts_thrown', 0)),
                                'total_points': int(points),
                                'average': to_float(player.get('average'), 0),
                                'first_nine_avg': to_float(player.get('first_nine_avg'), None),
                                'count_180s': player.get('count_180s', 0),
                                'count_140_plus': player.get('count_140_plus', 0),
                                'count_100_plus': player.get('count_100_plus', 0),
                                'highest_score': player.get('highest_score'),
                                'checkout_efficiency': player.get('checkout_efficiency', '-'),
                                'checkout_opportunities': player.get('checkout_opportunities', 0),
                                'checkouts_hit': player.get('checkouts_hit', 0),
                                'highest_checkout': player.get('highest_checkout'),
                                'avg_finish': to_float(player.get('avg_finish'), None),
                                'card_link': player.get('card_link')
                            }
                            
                            # Upsert to Supabase
                            supabase.table('aads_players').upsert(record).execute()
                            
                            # Track player for response
                            player_name = player.get('name')
                            if player_name not in results["players"]:
                                results["players"][player_name] = {
                                    'matches': 0,
                                    'total_legs': 0,
                                    'total_180s': 0,
                                    'total_140_plus': 0,
                                    'total_100_plus': 0
                                }
                            
                            results["players"][player_name]['matches'] += 1
                            results["players"][player_name]['total_legs'] += player.get('total_games', 0)
                            results["players"][player_name]['total_180s'] += player.get('count_180s', 0)
                            results["players"][player_name]['total_140_plus'] += player.get('count_140_plus', 0)
                            results["players"][player_name]['total_100_plus'] += player.get('count_100_plus', 0)
                        
                        results["successful"] += 1
                        progress_dict[job_id]["successful"] += 1
                        progress_dict[job_id]["players"] = {k: v['matches'] for k, v in results["players"].items()}
                        logger.info(f"[{job_id}] ✅ Match {i} complete")
                        break
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"No data: {match_id}")
                        progress_dict[job_id]["failed"] += 1
                        break
                        
                except Exception as e:
                    if attempt < MAX_RETRIES:
                        logger.warning(f"[{job_id}] Retry {attempt}/{MAX_RETRIES}")
                        time.sleep(5)
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Error: {match_id}")
                        progress_dict[job_id]["failed"] += 1
                        break
            
            # Delay between matches
            if i < len(match_urls):
                time.sleep(DELAY_BETWEEN_MATCHES)
        
        # Final progress update
        progress_dict[job_id]["status"] = "complete"
        progress_dict[job_id]["progress"] = 100
        progress_dict[job_id]["message"] = f"✅ Complete! Scraped {results['successful']}/{results['total_matches']} matches"
        progress_dict[job_id]["completed_at"] = datetime.now().isoformat()
        progress_dict[job_id]["final_results"] = {
            "total_matches": results["total_matches"],
            "successful": results["successful"],
            "failed": results["failed"],
            "total_players": len(results["players"]),
            "players": results["players"],
            "errors": results["errors"][:5]
        }
        
    except Exception as e:
        logger.error(f"[{job_id}] Scrape job failed: {e}")
        progress_dict[job_id]["status"] = "error"
        progress_dict[job_id]["message"] = f"❌ Error: {str(e)}"
        progress_dict[job_id]["errors"].append(str(e))
