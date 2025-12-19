#!/usr/bin/env python3
"""
INVESTIGATE DARTCONNECT TURN-BY-TURN DATA
Explore the DartConnect API to find endpoints that provide throw-by-throw data
"""

import requests
from bs4 import BeautifulSoup
import json
import html
import re
from pprint import pprint

def investigate_match_data(match_url):
    """
    Deep dive into match data structure to find turn-by-turn information
    """
    print("=" * 80)
    print("🔍 INVESTIGATING DARTCONNECT TURN-BY-TURN DATA")
    print("=" * 80)
    print(f"Match URL: {match_url}\n")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Get match ID from URL
    match_id = match_url.split('/')[-1]
    print(f"Match ID: {match_id}\n")
    
    # ========================================================================
    # 1. ANALYZE MAIN PAGE DATA
    # ========================================================================
    print("[1] Fetching main recap page...")
    response = session.get(match_url, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Get Inertia data
    app_div = soup.find('div', {'id': 'app'})
    if app_div and app_div.has_attr('data-page'):
        page_data = html.unescape(app_div['data-page'])
        data = json.loads(page_data)
        props = data.get('props', {})
        
        print(f"✅ Found Inertia.js data")
        print(f"   Available prop keys: {list(props.keys())}\n")
        
        # Look for turn data in props
        for key in props.keys():
            if 'turn' in key.lower() or 'throw' in key.lower() or 'score' in key.lower():
                print(f"   🎯 Found potential turn data key: {key}")
                print(f"      Type: {type(props[key])}")
                if isinstance(props[key], (list, dict)) and props[key]:
                    print(f"      Sample: {str(props[key])[:200]}...")
                print()
        
        # Check segments structure deeply
        segments = props.get('segments', {})
        if segments:
            print("\n[2] ANALYZING SEGMENTS STRUCTURE")
            print("-" * 80)
            
            for seg_key, seg_value in segments.items():
                if seg_value and len(seg_value) > 0 and seg_value[0]:
                    first_leg = seg_value[0][0] if isinstance(seg_value[0], list) and seg_value[0] else None
                    
                    if first_leg and isinstance(first_leg, dict):
                        print(f"\nSegment key: '{seg_key}'")
                        print(f"First leg keys: {list(first_leg.keys())}")
                        
                        # Look for turn/throw/score data
                        for leg_key in first_leg.keys():
                            if 'turn' in leg_key.lower() or 'throw' in leg_key.lower() or 'score' in leg_key.lower() or 'visit' in leg_key.lower():
                                print(f"   🎯 FOUND: {leg_key}")
                                print(f"      Value: {first_leg[leg_key]}")
                        
                        # Check home/away player data
                        if 'home' in first_leg:
                            home_keys = list(first_leg['home'].keys())
                            print(f"\n   Home player keys: {home_keys}")
                            
                            for hkey in home_keys:
                                if 'turn' in hkey.lower() or 'throw' in hkey.lower() or 'score' in hkey.lower() or 'visit' in hkey.lower():
                                    print(f"      🎯 FOUND in home: {hkey}")
                                    print(f"         Value: {first_leg['home'][hkey]}")
        
        # Save full props for manual inspection
        with open('full_props_dump.json', 'w') as f:
            json.dump(props, f, indent=2)
        print(f"\n💾 Full props saved to: full_props_dump.json")
    
    # ========================================================================
    # 2. TRY POTENTIAL API ENDPOINTS
    # ========================================================================
    print("\n" + "=" * 80)
    print("[3] TESTING POTENTIAL API ENDPOINTS")
    print("=" * 80)
    
    base_url = "https://recap.dartconnect.com"
    api_base = "https://tv.dartconnect.com/api"
    
    potential_endpoints = [
        f"{api_base}/match/{match_id}",
        f"{api_base}/match/{match_id}/details",
        f"{api_base}/match/{match_id}/turns",
        f"{api_base}/match/{match_id}/throws",
        f"{api_base}/match/{match_id}/visits",
        f"{api_base}/match/{match_id}/scores",
        f"{base_url}/api/match/{match_id}",
        f"{base_url}/api/match/{match_id}/details",
        f"{base_url}/api/match/{match_id}/turns",
        f"{base_url}/api/matches/{match_id}",
        f"{base_url}/api/matches/{match_id}/details",
    ]
    
    for endpoint in potential_endpoints:
        try:
            print(f"\nTrying: {endpoint}")
            resp = session.get(endpoint, timeout=10)
            
            if resp.status_code == 200:
                print(f"   ✅ SUCCESS! Status: {resp.status_code}")
                
                try:
                    json_data = resp.json()
                    print(f"   Response keys: {list(json_data.keys())}")
                    
                    # Save successful response
                    filename = f"api_response_{endpoint.split('/')[-1]}.json"
                    with open(filename, 'w') as f:
                        json.dump(json_data, f, indent=2)
                    print(f"   💾 Saved to: {filename}")
                    
                    # Look for turn data
                    def search_for_turns(obj, path=""):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                new_path = f"{path}.{key}" if path else key
                                if 'turn' in key.lower() or 'throw' in key.lower() or 'visit' in key.lower():
                                    print(f"      🎯 FOUND TURN DATA at {new_path}")
                                    print(f"         Type: {type(value)}")
                                    if isinstance(value, list) and len(value) > 0:
                                        print(f"         Sample: {value[0]}")
                                search_for_turns(value, new_path)
                        elif isinstance(obj, list) and len(obj) > 0:
                            search_for_turns(obj[0], f"{path}[0]")
                    
                    search_for_turns(json_data)
                    
                except Exception as e:
                    print(f"   Response text (first 500 chars): {resp.text[:500]}")
            else:
                print(f"   ❌ Status: {resp.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {type(e).__name__}")
    
    # ========================================================================
    # 4. SEARCH FOR ZIGGY ROUTES (API ROUTE DEFINITIONS)
    # ========================================================================
    print("\n" + "=" * 80)
    print("[4] SEARCHING ZIGGY ROUTES FOR API PATTERNS")
    print("=" * 80)
    
    if props and 'ziggy' in props:
        ziggy = props['ziggy']
        if 'routes' in ziggy:
            routes = ziggy['routes']
            
            print(f"\nFound {len(routes)} routes in Ziggy config")
            print("Searching for match/game/turn/visit related routes...\n")
            
            relevant_routes = []
            for route_name, route_data in routes.items():
                if any(keyword in route_name.lower() for keyword in ['match', 'game', 'turn', 'visit', 'score', 'throw']):
                    relevant_routes.append((route_name, route_data))
            
            if relevant_routes:
                print(f"Found {len(relevant_routes)} relevant routes:\n")
                for route_name, route_data in relevant_routes:
                    print(f"  📍 {route_name}")
                    print(f"     URI: {route_data.get('uri')}")
                    print(f"     Methods: {route_data.get('methods')}")
                    if 'parameters' in route_data:
                        print(f"     Parameters: {route_data['parameters']}")
                    print()
            else:
                print("No obvious turn/visit routes found in Ziggy config")
    
    print("\n" + "=" * 80)
    print("✅ INVESTIGATION COMPLETE")
    print("=" * 80)
    print("\nCheck the generated JSON files for detailed data structures")


if __name__ == "__main__":
    # Use a match from event 1
    test_match = "https://recap.dartconnect.com/matches/688e66b6f4fc02e124e759c8"
    investigate_match_data(test_match)
