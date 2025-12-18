"""
Updated _parse_alternative_format method for scraper.py
This replacement handles the actual DartConnect Inertia.js structure
"""

def _parse_alternative_format(self, soup):
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
