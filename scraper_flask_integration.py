"""
AADS Comprehensive Scraper - Flask Integration Version
This version integrates the working scraper logic with Flask progress tracking
and saves data to JSON instead of uploading to Supabase to avoid 400 errors
"""

import requests
import json
import logging
import time
from datetime import datetime
import threading

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# In-memory progress tracking (same as Flask app)
scrape_progress = {}

def update_progress(job_id, current_match, total_matches, status, stats=None):
    """Update progress for a scraping job"""
    scrape_progress[job_id] = {
        'current_match': current_match,
        'total_matches': total_matches,
        'status': status,
        'percentage': round((current_match / total_matches) * 100, 1) if total_matches > 0 else 0,
        'stats': stats or {}
    }
    logger.info(f"[{job_id}] {status} - Match {current_match}/{total_matches}")

def extract_match_urls_from_event(event_url, job_id):
    """Extract all match URLs from an event using DartConnect API2"""
    try:
        update_progress(job_id, 0, 27, f"Extracting match URLs from: {event_url}")
        
        # Parse event URL to get event ID - using regex like working scraper
        import re
        event_id_match = re.search(r'/event/([a-zA-Z0-9_]+)', event_url)
        if not event_id_match:
            raise ValueError("Could not extract event ID from URL")
        
        event_id = event_id_match.group(1)
        logger.info(f"[{job_id}] Event ID: {event_id}")
        
        # Use the correct API2 endpoint like working scraper
        api_url = f"https://tv.dartconnect.com/api2/event/{event_id}/matches"
        logger.info(f"[{job_id}] Calling API2: {api_url}")
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Referer': event_url
        }
        
        # Make POST request like working scraper
        response = requests.post(api_url, headers=headers, json={}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        match_urls = []
        
        # Extract all match IDs and construct recap URLs
        for match in data.get('matches', []):
            match_id = match.get('id')
            if match_id:
                recap_url = f"https://recap.dartconnect.com/matches/{match_id}"
                match_urls.append(recap_url)
        
        update_progress(job_id, 0, len(match_urls), f"Found {len(match_urls)} match URLs")
        logger.info(f"[{job_id}] Found {len(match_urls)} matches")
        return match_urls
        
    except Exception as e:
        logger.error(f"[{job_id}] Error extracting match URLs: {e}")
        update_progress(job_id, 0, 0, f"Error: Failed to extract match URLs - {str(e)}")
        return []

def scrape_single_match_comprehensive(match_url, job_id, match_index, total_matches):
    """Scrape comprehensive stats from a single match"""
    try:
        update_progress(job_id, match_index, total_matches, f"Match {match_index}/{total_matches}")
        
        # Get match ID from URL
        match_id = match_url.split('/')[-1]
        
        # Fetch player performance data
        players_url = f"https://recap.dartconnect.com/players/{match_id}"
        counts_url = f"https://recap.dartconnect.com/counts/{match_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': match_url
        }
        
        logger.info(f"Fetching Player Performance: {players_url}")
        players_response = requests.get(players_url, headers=headers, timeout=30)
        players_response.raise_for_status()
        
        logger.info(f"Fetching Match Counts: {counts_url}")
        counts_response = requests.get(counts_url, headers=headers, timeout=30)
        counts_response.raise_for_status()
        
        players_data = players_response.json()
        counts_data = counts_response.json()
        
        # Process the data
        match_players = []
        
        for player_data in players_data.get('players', []):
            player_name = player_data.get('name', '')
            
            # Get counts for this player
            player_counts = next((c for c in counts_data.get('players', []) if c.get('name') == player_name), {})
            
            # Calculate comprehensive stats
            legs = player_data.get('legs', [])
            total_darts = sum(leg.get('darts', 0) for leg in legs)
            total_score = sum(leg.get('score', 0) for leg in legs)
            
            # 3-dart average
            three_dart_avg = (total_score / total_darts * 3) if total_darts > 0 else 0
            
            # First 9 average from first 3 darts of each leg
            first_9_scores = []
            for leg in legs:
                throws = leg.get('throws', [])
                if throws:
                    first_throw = throws[0] if len(throws) > 0 else 0
                    first_9_scores.append(first_throw)
            first_9_avg = sum(first_9_scores) if first_9_scores else 0
            
            # Checkout stats
            legs_won = len([leg for leg in legs if leg.get('won', False)])
            legs_played = len(legs)
            legs_lost = legs_played - legs_won
            
            checkout_attempts = 0
            successful_checkouts = 0
            checkout_total = 0
            high_finish = 0
            
            for leg in legs:
                if leg.get('won', False):
                    checkout_score = leg.get('checkout', 0)
                    if checkout_score > 0:
                        successful_checkouts += 1
                        checkout_total += checkout_score
                        high_finish = max(high_finish, checkout_score)
                
                # Count checkout attempts (legs where player got below 170)
                if leg.get('ending_points', 501) < 170:
                    checkout_attempts += 1
            
            checkout_average = (checkout_total / successful_checkouts) if successful_checkouts > 0 else 0
            checkout_success_rate = (successful_checkouts / checkout_attempts) if checkout_attempts > 0 else 0
            
            # Count high scores from player_counts
            one_eighties = player_counts.get('180s', 0) or player_counts.get('180_count', 0)
            one_forty_plus = player_counts.get('140_plus', 0) or player_counts.get('140_plus_count', 0)
            hundreds_plus = player_counts.get('100_plus', 0) or player_counts.get('100_plus_count', 0)
            
            # Checkout categories
            checkout_100_plus = len([leg for leg in legs if leg.get('checkout', 0) >= 100])
            checkout_170 = len([leg for leg in legs if leg.get('checkout', 0) == 170])
            
            # Process leg details
            legs_detail = []
            for i, leg in enumerate(legs):
                legs_detail.append({
                    'leg_number': i + 1,
                    'ppr': (leg.get('score', 0) / leg.get('darts', 1) * 3) if leg.get('darts', 0) > 0 else 0,
                    'starting_points': 501,  # Standard 501 game
                    'ending_points': leg.get('ending_points', 0),
                    'checkout': leg.get('checkout', 0),
                    'won': leg.get('won', False),
                    'darts_thrown': leg.get('darts', 0)
                })
            
            player_stats = {
                'player_name': player_name,
                'three_dart_avg': round(three_dart_avg, 2),
                'first_9_avg': round(first_9_avg, 2),
                'legs_played': legs_played,
                'legs_won': legs_won,
                'legs_lost': legs_lost,
                'leg_win_percentage': round((legs_won / legs_played * 100), 2) if legs_played > 0 else 0,
                'checkout_average': round(checkout_average, 2),
                'checkout_attempts': checkout_attempts,
                'successful_checkouts': successful_checkouts,
                'checkout_success_rate': round(checkout_success_rate * 100, 2),
                'checkout_100_plus': checkout_100_plus,
                'checkout_170': checkout_170,
                'high_finish': high_finish,
                'one_eighties': one_eighties,
                'one_forty_plus': one_forty_plus,
                'hundreds_plus': hundreds_plus,
                'legs_detail': legs_detail
            }
            
            match_players.append(player_stats)
        
        result = {
            'players': match_players,
            'match_url': match_url
        }
        
        logger.info(f"✅ Successfully scraped {len(match_players)} players")
        return result
        
    except Exception as e:
        logger.error(f"[{job_id}] Error scraping match {match_url}: {e}")
        return None

def scrape_full_event_comprehensive_flask(event_url, job_id):
    """Complete event scraping with Flask progress integration"""
    try:
        # Extract all match URLs
        match_urls = extract_match_urls_from_event(event_url, job_id)
        if not match_urls:
            update_progress(job_id, 0, 0, "Error: No matches found")
            return
        
        update_progress(job_id, 0, len(match_urls), f"Scraping {len(match_urls)} matches with comprehensive stats")
        
        all_results = []
        successful_scrapes = 0
        
        for i, match_url in enumerate(match_urls, 1):
            result = scrape_single_match_comprehensive(match_url, job_id, i, len(match_urls))
            if result:
                all_results.append(result)
                successful_scrapes += 1
        
        # Save results to JSON file
        output_file = f"flask_scrape_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = {
            'event_url': event_url,
            'total_matches': len(match_urls),
            'successful_scrapes': successful_scrapes,
            'timestamp': datetime.now().isoformat(),
            'matches': all_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Calculate aggregated stats
        total_players = sum(len(match['players']) for match in all_results)
        avg_score = sum(
            player['three_dart_avg'] 
            for match in all_results 
            for player in match['players']
        ) / total_players if total_players > 0 else 0
        
        total_180s = sum(
            player['one_eighties'] 
            for match in all_results 
            for player in match['players']
        )
        
        final_stats = {
            'total_players': total_players,
            'total_180s': total_180s,
            'average_score': round(avg_score, 2),
            'output_file': output_file
        }
        
        update_progress(job_id, len(match_urls), len(match_urls), 
                       f"✅ Completed! Scraped {successful_scrapes}/{len(match_urls)} matches. Saved to {output_file}", 
                       final_stats)
        
        logger.info(f"[{job_id}] Scraping completed! Results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"[{job_id}] Fatal error in scraping: {e}")
        update_progress(job_id, 0, 0, f"Error: {str(e)}")

def start_background_scrape(event_url):
    """Start a background scrape with progress tracking"""
    # Generate job ID from timestamp and event URL
    timestamp = int(time.time())
    job_id = f"{timestamp}_{event_url.split('/')[-1]}"
    
    # Start scraping in background thread
    thread = threading.Thread(
        target=scrape_full_event_comprehensive_flask, 
        args=(event_url, job_id)
    )
    thread.daemon = True
    thread.start()
    
    return job_id

def get_progress(job_id):
    """Get current progress for a job"""
    return scrape_progress.get(job_id, {
        'status': 'Job not found',
        'current_match': 0,
        'total_matches': 0,
        'percentage': 0,
        'stats': {}
    })

# Test the system
if __name__ == "__main__":
    event_url = "https://tv.dartconnect.com/event/mt_joe6163l_1"
    
    print("Testing Flask Integration Scraper...")
    print("This will scrape Event #1 and save results to JSON file")
    print("Progress will be logged to console")
    
    job_id = start_background_scrape(event_url)
    print(f"Started job: {job_id}")
    
    # Monitor progress
    while True:
        progress = get_progress(job_id)
        print(f"Status: {progress['status']} - {progress['percentage']}%")
        
        if progress['percentage'] >= 100 or 'Error:' in progress['status'] or 'Completed!' in progress['status']:
            break
        
        time.sleep(5)
    
    print("Scraping completed!")
    print(f"Final status: {progress['status']}")
    if 'stats' in progress:
        print(f"Final stats: {progress['stats']}")