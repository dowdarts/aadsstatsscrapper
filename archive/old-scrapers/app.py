"""
AADS Flask Server
Web API and dashboard for Atlantic Amateur Darts Series statistics
Manual stats input with Supabase backend - No scraping
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from database_manager import AADSDataManager
import logging
import os
from typing import Dict, List
from datetime import datetime
import json

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


# Initialize database manager
db_manager = AADSDataManager()


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


    # Removed scraping-related endpoint


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
        "version": "2.0.0 - Manual Input System"
    })

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


# ============================================================================
# NEW ROUTES FOR MANUAL STATS INPUT & SUPABASE BACKEND
# ============================================================================

@app.route('/stats-input')
def stats_input():
    """Serve the stats input admin interface."""
    return render_template('stats_input.html')


@app.route('/admin/save-tournament', methods=['POST'])
def save_tournament():
    """
    Save complete tournament data (draft or published).
    
    Request JSON:
        {
            "series_name": "Series 1",
            "year": 2025,
            "event_number": 1,
            "event_date": "2025-01-15",
            "players": [...],
            "matches": [...],
            "is_draft": true/false
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        is_draft = data.get('is_draft', True)
        
        # Save tournament using database manager
        event_id = db_manager.save_tournament(data, is_draft=is_draft)
        
        return jsonify({
            "success": True,
            "event_id": event_id,
            "message": "Draft saved" if is_draft else "Published successfully"
        })
        
    except Exception as e:
        logger.error(f"Error saving tournament: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/admin/load-event/<event_id>')
def load_event(event_id):
    """
    Load complete tournament data for editing.
    
    Returns:
        JSON with tournament data including players, matches, stats
    """
    try:
        tournament = db_manager.load_tournament(event_id)
        
        if not tournament:
            return jsonify({"success": False, "error": "Event not found"}), 404
        
        return jsonify({
            "success": True,
            "tournament": tournament
        })
        
    except Exception as e:
        logger.error(f"Error loading event: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/stats-version')
def get_stats_version():
    """
    Get current published version number for auto-refresh polling.
    
    Returns:
        JSON with version number
    """
    try:
        version = db_manager.get_current_version()
        return jsonify({
            "success": True,
            "version": version
        })
    except Exception as e:
        logger.error(f"Error getting version: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/all-time-standings')
def get_all_time_standings():
    """
    Get all-time career standings ranked by legs won percentage.
    
    Returns:
        JSON with player career statistics
    """
    try:
        standings = db_manager.get_all_time_standings()
        return jsonify({
            "success": True,
            "standings": standings
        })
    except Exception as e:
        logger.error(f"Error getting standings: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/series')
def get_series_list():
    """Get list of all series."""
    try:
        series = db_manager.get_all_series()
        return jsonify({
            "success": True,
            "series": series
        })
    except Exception as e:
        logger.error(f"Error getting series: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/events-list')
def get_events_list():
    """
    Get list of all events with series info.
    
    Query Parameters:
        status: 'draft', 'published', or omit for all
    """
    try:
        status = request.args.get('status')
        events = db_manager.get_all_events(status=status)
        
        return jsonify({
            "success": True,
            "events": events
        })
    except Exception as e:
        logger.error(f"Error getting events: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/player/<player_id>')
def get_player_profile(player_id):
    """
    Get complete player profile with stats.
    
    Returns:
        JSON with player info, dart setup, and career stats
    """
    try:
        player = db_manager.get_player(player_id)
        
        if not player:
            return jsonify({"success": False, "error": "Player not found"}), 404
        
        # Get career stats
        career_stats = db_manager.calculate_career_stats(player_id)
        
        # Get personal best
        personal_best = db_manager.get_player_personal_best(player_id)
        
        return jsonify({
            "success": True,
            "player": player,
            "career_stats": career_stats,
            "personal_best": personal_best
        })
    except Exception as e:
        logger.error(f"Error getting player: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/players')
def get_all_players_list():
    """Get list of all players."""
    try:
        players = db_manager.get_all_players()
        return jsonify({
            "success": True,
            "players": players
        })
    except Exception as e:
        logger.error(f"Error getting players: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/admin/backup-data')
def backup_data():
    """
    Export complete database as JSON for backup.
    
    Returns:
        JSON file download with timestamp
    """
    try:
        data = db_manager.export_all_data()
        
        # Create timestamped filename
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = f'aads_backup_{timestamp}.json'
        
        response = jsonify(data)
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Content-Type'] = 'application/json'
        
        return response
        
    except Exception as e:
        logger.error(f"Error backing up data: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/admin/restore-backup', methods=['POST'])
def restore_backup():
    """
    Restore data from backup JSON.
    
    Request: JSON data from backup file
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        db_manager.import_data(data)
        
        return jsonify({
            "success": True,
            "message": "Data restored successfully"
        })
        
    except Exception as e:
        logger.error(f"Error restoring backup: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/stats-export', methods=['POST'])
def export_stats():
    """
    Export stats in various formats (PDF, CSV, JSON).
    
    Request JSON:
        {
            "format": "pdf|csv|json",
            "scope": "all|series|event|player",
            "scope_id": "optional UUID"
        }
    """
    try:
        data = request.get_json()
        format_type = data.get('format', 'json')
        scope = data.get('scope', 'all')
        
        # This would generate the export
        # For now, return placeholder
        return jsonify({
            "success": True,
            "message": f"Export to {format_type} coming soon",
            "format": format_type,
            "scope": scope
        })
        
    except Exception as e:
        logger.error(f"Error exporting stats: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/docs/official_stats_display.html')
def official_stats_display():
    """Serve the official stats display page."""
    return send_from_directory('docs', 'official_stats_display.html')


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
