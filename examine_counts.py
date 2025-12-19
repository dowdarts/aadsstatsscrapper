#!/usr/bin/env python3
"""
Examine the counts endpoint to find detailed scoring breakdowns
"""

import requests
from bs4 import BeautifulSoup
import json
import html

def examine_counts_data(match_id):
    """Examine what data is available in the counts endpoint"""
    
    url = f"https://recap.dartconnect.com/counts/{match_id}"
    print(f"🔍 Examining counts endpoint: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        app_div = soup.find('div', {'id': 'app'})
        
        if not app_div or 'data-page' not in app_div.attrs:
            print("❌ No data-page found")
            return
        
        data_page = app_div['data-page']
        data_page = html.unescape(data_page)
        page_data = json.loads(data_page)
        
        props = page_data.get('props', {})
        
        print(f"\n📊 All props keys:")
        for key in props.keys():
            print(f"  - {key}")
        
        # Look for players or performance data
        if 'players' in props:
            players = props['players']
            print(f"\n👥 Found {len(players)} players")
            
            for i, player in enumerate(players):
                print(f"\n🎯 Player {i+1}: {player.get('name', 'Unknown')}")
                print(f"  Keys: {list(player.keys())}")
                
                # Look for scoring data
                for key, value in player.items():
                    if any(term in key.lower() for term in ['count', 'score', '180', '140', '100', 'dart', 'throw']):
                        print(f"  🎯 {key}: {value}")
                
                # Print first 5 key-value pairs for examination
                if i == 0:
                    print(f"\n  📋 First player detailed data:")
                    for j, (key, value) in enumerate(player.items()):
                        if j < 10:  # Show first 10 items
                            print(f"    {key}: {value}")
                        else:
                            print(f"    ... ({len(player)} total items)")
                            break
        
        # Also check for playerPerformances
        if 'playerPerformances' in props:
            performances = props['playerPerformances']
            print(f"\n🎭 Found playerPerformances with {len(performances)} entries")
            
            for i, perf in enumerate(performances):
                print(f"\n🎯 Performance {i+1}:")
                print(f"  Keys: {list(perf.keys())}")
                
                # Look for player name
                if 'player' in perf:
                    print(f"  Player: {perf['player']}")
                
                # Look for counts/scoring data  
                for key, value in perf.items():
                    if any(term in key.lower() for term in ['count', 'score', '180', '140', '100', 'plus', 'dart', 'throw']):
                        print(f"  🎯 {key}: {value}")
                
                # Show detailed structure for first performance
                if i == 0:
                    print(f"\n  📋 First performance detailed structure:")
                    for key, value in perf.items():
                        if isinstance(value, dict):
                            print(f"    {key}: {{...}} (dict with keys: {list(value.keys())})")
                        elif isinstance(value, list):
                            print(f"    {key}: [...] (list with {len(value)} items)")
                        else:
                            print(f"    {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    examine_counts_data("688e66b6f4fc02e124e759c8")