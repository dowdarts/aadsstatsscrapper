"""
AADS Flask Server
Web API and dashboard for Atlantic Amateur Darts Series statistics
With comprehensive advanced stats scraping (180s, 140+, 100+, checkout stats, etc.)
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from database_manager import AADSDataManager
from scraper import DartConnectScraper
import logging
import os
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Initialize database manager and scraper
db_manager = AADSDataManager()
scraper = DartConnectScraper()


@app.route('/')
def index():
    """
    Serve the main standings dashboard.
    
    Returns:
        Rendered HTML template
    """
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """
    API endpoint to get current standings and statistics.
    
    Query Parameters:
        sort_by (optional): Metric to sort by (default: weighted_3da)
        player (optional): Get stats for specific player
    
    Returns:
        JSON response with player statistics
    """
    try:
        # Check if requesting specific player
        player_name = request.args.get('player')
        if player_name:
            player_stats = db_manager.get_player_stats(player_name)
            if player_stats:
                return jsonify({
                    "success": True,
                    "player": player_stats
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Player not found"
                }), 404
        
        # Get leaderboard
        sort_by = request.args.get('sort_by', 'weighted_3da')
        leaderboard = db_manager.get_leaderboard(sort_by=sort_by)
        
        # Get series info
        series_info = db_manager.data.get('series_info', {})
        
        return jsonify({
            "success": True,
            "series_info": series_info,
            "leaderboard": leaderboard,
            "total_players": len(leaderboard),
            "last_updated": db_manager.data.get('last_updated')
        })
    
    except Exception as e:
        logger.error(f"Error in /api/stats: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/qualified')
def get_qualified():
    """
    API endpoint to get players qualified for Tournament of Champions.
    
    Returns:
        JSON response with qualified players
    """
    try:
        qualified_players = db_manager.get_qualified_players()
        
        return jsonify({
            "success": True,
            "qualified_players": qualified_players,
            "total_qualified": len(qualified_players)
        })
    
    except Exception as e:
        logger.error(f"Error in /api/qualified: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/events')
def get_events():
    """
    API endpoint to get event information.
    
    Query Parameters:
        event_id (optional): Get specific event details
    
    Returns:
        JSON response with event information
    """
    try:
        event_id = request.args.get('event_id')
        
        if event_id:
            event_details = db_manager.get_event_details(int(event_id))
            if event_details:
                return jsonify({
                    "success": True,
                    "event": event_details
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Event not found"
                }), 404
        
        # Return all events
        return jsonify({
            "success": True,
            "events": db_manager.data.get('events', {})
        })
    
    except Exception as e:
        logger.error(f"Error in /api/events: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/scrape', methods=['POST'])
def scrape_url():
    """
    API endpoint to scrape a DartConnect URL and add stats to database.
    
    Request JSON:
        {
            "url": "DartConnect Match Recap URL",
            "event_id": Event number (1-7)
        }
    
    Returns:
        JSON response with scraping results
    """
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'url' in request"
            }), 400
        
        url = data['url']
        event_id = data.get('event_id', 1)
        
        # Scrape the URL
        logger.info(f"API scrape request for URL: {url}")
        player_stats = scraper.scrape_match_recap(url)
        
        if not player_stats:
            return jsonify({
                "success": False,
                "error": "Failed to scrape URL or no data found"
            }), 400
        
        # Add stats to database
        added_players = []
        for stats in player_stats:
            player_name = stats.pop('player_name')
            db_manager.add_match_stats(player_name, event_id, stats)
            added_players.append(player_name)
        
        return jsonify({
            "success": True,
            "message": f"Added stats for {len(added_players)} player(s)",
            "players": added_players,
            "event_id": event_id
        })
    
    except Exception as e:
        logger.error(f"Error in /api/scrape: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/add-stats', methods=['POST'])
def add_stats_manual():
    """
    API endpoint to manually add player statistics.
    
    Request JSON:
        {
            "player_name": "Player Name",
            "event_id": Event number (1-7),
            "stats": {
                "three_dart_avg": 75.5,
                "legs_played": 5,
                "first_9_avg": 80.2,
                "hundreds_plus": 12,
                "one_forty_plus": 4,
                "one_eighties": 2,
                "high_finish": 120
            }
        }
    
    Returns:
        JSON response confirming addition
    """
    try:
        data = request.get_json()
        
        if not data or 'player_name' not in data or 'stats' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required fields"
            }), 400
        
        player_name = data['player_name']
        event_id = data.get('event_id', 1)
        stats = data['stats']
        
        db_manager.add_match_stats(player_name, event_id, stats)
        
        return jsonify({
            "success": True,
            "message": f"Stats added for {player_name}",
            "player_name": player_name,
            "event_id": event_id
        })
    
    except Exception as e:
        logger.error(f"Error in /api/add-stats: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/set-winner', methods=['POST'])
def set_winner():
    """
    API endpoint to set the winner of an event.
    
    Request JSON:
        {
            "event_id": Event number (1-7),
            "player_name": "Winner Name"
        }
    
    Returns:
        JSON response confirming winner
    """
    try:
        data = request.get_json()
        
        if not data or 'event_id' not in data or 'player_name' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required fields"
            }), 400
        
        event_id = data['event_id']
        player_name = data['player_name']
        
        db_manager.set_event_winner(event_id, player_name)
        
        return jsonify({
            "success": True,
            "message": f"{player_name} set as winner of Event {event_id}",
            "event_id": event_id,
            "winner": player_name
        })
    
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error in /api/set-winner: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/health')
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with service status
    """
    return jsonify({
        "status": "healthy",
        "service": "AADS Stats API",
        "version": "1.0.0"
    })

@app.route('/api/scrape-event', methods=['POST'])
def scrape_event():
    """
    COMPREHENSIVE TWO-PART EVENT SCRAPER WITH ADVANCED STATS
    
    PART 1: Extract match URLs using DartConnect API2
    PART 2: Scrape individual match recaps with ALL advanced statistics:
            - 180s, 140+, 100+ counts
            - First 9 average
            - Checkout efficiency and stats
            - Per-match records (not aggregated)
    """
    try:
        data = request.get_json()
        event_url = data.get('event_url')
        event_name = data.get('event_name', 'AADS Event')
        
        if not event_url:
            return jsonify({
                "success": False,
                "message": "Event URL is required"
            }), 400
        
        import json
        import time
        import re
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        from scraper_comprehensive import scrape_match_comprehensive
        from supabase import create_client
        
        # Supabase config
        SUPABASE_URL = "https://kswwbqumgsdissnwuiab.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtzd3dicXVtZ3NkaXNzbnd1aWFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ0ODMwNTIsImV4cCI6MjA4MDA1OTA1Mn0.b-z8JqL1dBYJcrrzSt7u6VAaFAtTOl1vqqtFFgHkJ50"
        USER_ID = "116cc929-d60f-4ae4-ac53-b228b91ea8b3"
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # ========================================================================
        # PART 1: EXTRACT MATCH URLs USING API2
        # ========================================================================
        logger.info(f"[PART 1] Extracting match URLs from: {event_url}")
        
        # Extract event ID from URL
        event_id_match = re.search(r'/event/([a-zA-Z0-9_]+)', event_url)
        if not event_id_match:
            return jsonify({
                "success": False,
                "message": "Could not extract event ID from URL"
            }), 400
        
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
            logger.error(f"[PART 1] Failed to call API2: {e}")
            return jsonify({
                "success": False,
                "message": f"Failed to extract matches: {str(e)}"
            }), 500
        
        # Extract match URLs from API2 payload
        match_urls = []
        payload = result.get('payload', {})
        
        # Iterate through all sections (completed, pending, etc.)
        for section_name, section_data in payload.items():
            if isinstance(section_data, list):
                for match in section_data:
                    if isinstance(match, dict) and 'mi' in match:
                        match_id = match['mi']
                        match_urls.append(f"https://recap.dartconnect.com/matches/{match_id}")
        
        if not match_urls:
            return jsonify({
                "success": False,
                "message": "No match URLs found in event"
            })
        
        logger.info(f"[PART 1] Found {len(match_urls)} match URLs")
        
        # ========================================================================
        # PART 2: SCRAPE COMPREHENSIVE STATS FROM MATCH TABS
        # ========================================================================
        logger.info(f"[PART 2] Scraping {len(match_urls)} matches with comprehensive stats")
        
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
            logger.info(f"[PART 2] Match {i}/{len(match_urls)}")
            
            # Extract match ID
            match_id_match = re.search(r'/matches/([a-f0-9]+)', url)
            if not match_id_match:
                results["failed"] += 1
                results["errors"].append(f"Invalid URL: {url}")
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
                        logger.info(f"✅ Match {i} complete")
                        break
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"No data: {match_id}")
                        break
                        
                except Exception as e:
                    if attempt < MAX_RETRIES:
                        logger.warning(f"Retry {attempt}/{MAX_RETRIES}")
                        time.sleep(5)
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Error: {match_id}")
                        break
            
            # Delay between matches
            if i < len(match_urls):
                time.sleep(DELAY_BETWEEN_MATCHES)
        
        return jsonify({
            "success": True,
            "message": f"Scraped {results['successful']}/{results['total_matches']} matches with comprehensive stats",
            "data": {
                "total_matches": results["total_matches"],
                "successful": results["successful"],
                "failed": results["failed"],
                "total_players": len(results["players"]),
                "players": results["players"],
                "errors": results["errors"][:5]  # Limit errors in response
            }
        })
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/reset-database', methods=['POST'])
def reset_database():
    """
    Reset the database (clear all data)
    """
    try:
        data = request.get_json() or {}
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                "success": False,
                "message": "Confirmation required to reset database"
            }), 400
        
        db_manager.reset_database()
        
        return jsonify({
            "success": True,
            "message": "Database reset successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error resetting database: {str(e)}"
        }), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {e}", exc_info=True)
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Run the Flask app
    logger.info("Starting AADS Flask Server...")
    logger.info("Dashboard available at: http://localhost:5000")
    logger.info("API available at: http://localhost:5000/api/stats")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
