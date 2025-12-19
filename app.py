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
import threading
import time
from datetime import datetime

# Import the working scraper progress system
from scraper_html_parser import scrape_event_comprehensive
from scraper_flask_integration import scrape_progress

# Import the NEW comprehensive two-stage scraper
from comprehensive_dart_scraper import TwoStageDartScraper

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
comprehensive_scraper = TwoStageDartScraper(delay=1.0)  # Fast scraping for live updates


@app.route('/')
def index():
    """
    Serve the main admin interface (GitHub Pages style).
    
    Returns:
        Rendered HTML file from docs folder
    """
    return send_from_directory('docs', 'index.html')

@app.route('/test')
def test_page():
    """Simple test page to verify server is working"""
    return send_from_directory('.', 'test_simple.html')

@app.route('/stats-display.html')
def stats_display():
    """
    Serve the stats display page.
    
    Returns:
        Rendered HTML file from docs folder
    """
    return send_from_directory('docs', 'stats-display.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from docs folder"""
    return send_from_directory('docs', filename)


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

@app.route('/api/scrape-progress/<job_id>', methods=['GET'])
def get_scrape_progress(job_id):
    """
    Get real-time progress of a scraping job.
    
    Returns:
        JSON response with scraping progress, stats, and status
    """
    from scraper_flask_integration import get_progress
    progress_data = get_progress(job_id)
    
    if progress_data.get('status') == 'Job not found':
        return jsonify({
            "success": False,
            "message": "Job not found"
        }), 404
    
    return jsonify(progress_data)

@app.route('/api/scrape-comprehensive', methods=['POST'])
def scrape_comprehensive():
    """
    NEW COMPREHENSIVE TWO-STAGE DART SCRAPER
    
    This endpoint uses the updated comprehensive scraper that extracts:
    - All basic stats (3DA, legs won/lost, etc.)
    - Detailed scoring breakdowns (100+, 120+, 140+, 160+, 180s)  
    - Performance metrics (first 9 average, highest score)
    - Finishing stats (checkout %, highest checkout, 100+ finishes)
    - Tournament bracket information
    
    Returns results immediately and integrates with database.
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
        
        logger.info(f"🚀 Starting comprehensive scrape for: {event_url}")
        
        # Run the comprehensive scraper
        df = comprehensive_scraper.run_full_scrape(event_url)
        
        if df.empty:
            return jsonify({
                "success": False,
                "message": "No data extracted from event"
            }), 400
        
        # Convert DataFrame to database format and add to DB
        added_players = []
        total_records = len(df)
        
        for _, row in df.iterrows():
            # Convert row data to database format
            stats_dict = {
                'three_dart_avg': row.get('3da', 0),
                'legs_played': row.get('legs_played', 0),
                'first_9_avg': row.get('first_nine_average', 0),
                'hundreds_plus': row.get('100_plus', 0),
                'one_forty_plus': row.get('140_plus', 0),
                'one_eighties': row.get('180s', 0),
                'high_finish': row.get('highest_checkout', 0),
                # Additional advanced stats
                'win_percentage': row.get('win_percentage', 0),
                'checkout_percentage': row.get('checkout_percentage', 0),
                'highest_score': row.get('highest_score', 0),
                'points_scored': row.get('points_scored', 0),
                'darts_thrown': row.get('darts_thrown', 0),
            }
            
            player_name = row.get('player_name', '')
            if player_name:
                db_manager.add_match_stats(player_name, event_id, stats_dict)
                if player_name not in added_players:
                    added_players.append(player_name)
        
        # Get tournament bracket info if available
        bracket_info = {}
        if hasattr(df, 'attrs') and 'tournament_results' in df.attrs:
            bracket_info = df.attrs['tournament_results']
        
        return jsonify({
            "success": True,
            "message": f"Successfully scraped and added {total_records} player records",
            "players_added": added_players,
            "total_records": total_records,
            "unique_players": len(added_players),
            "tournament_info": bracket_info
        })
        
    except Exception as e:
        logger.error(f"❌ Comprehensive scrape failed: {e}")
        return jsonify({
            "success": False,
            "message": f"Scraping failed: {str(e)}"
        }), 500

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
    
    Returns job_id immediately and runs scraping in background thread.
    Poll /api/scrape-progress/<job_id> to get real-time progress.
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
        
        # Generate job ID
        job_id = f"{int(time.time())}_{event_name.replace(' ', '_').replace('#', '')}"
        
        # Start background thread with working scraper
        from scraper_flask_integration import scrape_full_event_comprehensive_flask
        thread = threading.Thread(
            target=scrape_full_event_comprehensive_flask, 
            args=(event_url, job_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "message": "Scraping started - poll /api/scrape-progress/" + job_id + " for progress"
        })
        
    except Exception as e:
        logger.error(f"Failed to start scrape: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
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
