#!/usr/bin/env python3
"""
Debug script to examine the structure of DartConnect data
to understand how to extract 100+, 140+, 160+ counts
"""

import requests
from bs4 import BeautifulSoup
import json
import html

def debug_dartconnect_data_structure(match_url):
    """Examine the raw data structure from a match"""
    
    print(f"🔍 Debugging data structure for: {match_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    try:
        response = requests.get(match_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        app_div = soup.find('div', {'id': 'app'})
        
        if not app_div or 'data-page' not in app_div.attrs:
            print("❌ No data-page found")
            return
        
        data_page = app_div['data-page']
        data_page = html.unescape(data_page)
        page_data = json.loads(data_page)
        
        print("\n📊 Top-level keys:")
        for key in page_data.keys():
            print(f"  - {key}")
        
        # Look at props structure
        props = page_data.get('props', {})
        print(f"\n🎯 Props keys:")
        for key in props.keys():
            print(f"  - {key}")
        
        # Look at players data instead
        if 'players' in props:
            players = props['players']
            print(f"\n👥 Found {len(players)} players")
            
            for i, player in enumerate(players):
                print(f"\n🎯 Player {i+1} structure:")
                for key in player.keys():
                    value = player[key]
                    if isinstance(value, dict):
                        print(f"  - {key}: {{...}} (dict with {len(value)} keys)")
                        # Show dict keys
                        for sub_key in value.keys():
                            print(f"    - {sub_key}")
                    elif isinstance(value, list):
                        print(f"  - {key}: [...] (list with {len(value)} items)")
                    else:
                        print(f"  - {key}: {value}")
                
                # Look specifically for scoring data
                if i == 0:  # Just examine first player in detail
                    print(f"\n🔍 Detailed examination of player 1:")
                    for key, value in player.items():
                        if isinstance(value, dict) and ('score' in key.lower() or 'dart' in key.lower() or 'throw' in key.lower() or 'count' in key.lower()):
                            print(f"  🎯 {key}:")
                            for sub_key, sub_value in value.items():
                                print(f"    - {sub_key}: {sub_value}")
        
        else:
            print("❌ No 'players' key in props")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Use a known working match URL from the event
    test_url = "https://recap.dartconnect.com/players/688e66b6f4fc02e124e759c8"
    debug_dartconnect_data_structure(test_url)