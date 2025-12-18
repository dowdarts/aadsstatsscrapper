"""
AADS Flask Server
Web API and dashboard for Atlantic Amateur Darts Series statistics
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
    Extract and scrape all matches from an event page
    """
    try:
        data = request.get_json()
        event_url = data.get('event_url')
        event_id = data.get('event_id', 1)
        
        if not event_url:
            return jsonify({
                "success": False,
                "message": "Event URL is required"
            }), 400
        
        # Import here to avoid circular imports
        import requests
        from bs4 import BeautifulSoup
        import re
        import html as html_module
        
        # Extract match URLs from event page
        def extract_match_urls(url):
            response = requests.get(url)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            match_urls = []
            
            # Check Inertia.js data
            app_div = soup.find('div', {'id': 'app'})
            if app_div and app_div.has_attr('data-page'):
                try:
                    page_data_encoded = app_div['data-page']
                    page_data = html_module.unescape(page_data_encoded)
                    
                    # Search for match IDs (24-character hex strings)
                    match_id_pattern = r'[0-9a-f]{24}'
                    match_ids = re.findall(match_id_pattern, page_data)
                    
                    # Filter and deduplicate
                    unique_ids = list(set(match_ids))
                    filtered_ids = [mid for mid in unique_ids if len(set(mid)) > 3]
                    
                    for match_id in filtered_ids:
                        match_urls.append(f"https://recap.dartconnect.com/matches/{match_id}")
                
                except Exception:
                    pass
            
            return list(set(match_urls))
        
        match_urls = extract_match_urls(event_url)
        
        if not match_urls:
            return jsonify({
                "success": False,
                "message": "No match URLs found on event page"
            })
        
        # Scrape each match
        scraper = DartConnectScraper()
        results = {
            "total_matches": len(match_urls),
            "successful": 0,
            "failed": 0,
            "players_added": [],
            "errors": []
        }
        
        for url in match_urls:
            try:
                players = scraper.scrape_match_recap(url)
                
                if players:
                    # Add to database
                    for player in players:
                        db_manager.add_match_stats(
                            player_name=player['player_name'],
                            event_id=event_id,
                            three_dart_avg=player['three_dart_avg'],
                            legs_played=player['legs_played'],
                            one_eighties=player['one_eighties'],
                            high_finish=player['high_finish']
                        )
                        
                        if player['player_name'] not in results["players_added"]:
                            results["players_added"].append(player['player_name'])
                    
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"No data found: {url}")
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error scraping {url}: {str(e)}")
        
        return jsonify({
            "success": True,
            "message": f"Scraped {results['successful']} of {results['total_matches']} matches",
            "data": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error processing event: {str(e)}"
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
