#!/usr/bin/env python3
"""
Deep dive into the dist (distribution) data structure to find 100+, 140+, 160+, 180s
"""

import requests
from bs4 import BeautifulSoup
import json
import html

def examine_dist_structure(match_id):
    """Examine the distribution data structure in detail"""
    
    url = f"https://recap.dartconnect.com/counts/{match_id}"
    print(f"🔍 Deep diving into dist structure: {url}")
    
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
        performances = props.get('playerPerformances', [])
        
        for i, perf in enumerate(performances):
            player_name = perf.get('name', 'Unknown')
            print(f"\n🎯 Player {i+1}: {player_name}")
            
            # Extract all the key stats
            first_nine = perf.get('first_nine', 0)
            checkout_efficiency = perf.get('coe', '0%')
            
            print(f"  First 9 Average: {first_nine}")
            print(f"  Checkout Efficiency: {checkout_efficiency}")
            
            # Examine double_out_stats
            double_out = perf.get('double_out_stats', {})
            print(f"  🎯 Double Out Stats:")
            for key, value in double_out.items():
                print(f"    {key}: {value}")
            
            # Examine distribution data
            dist = perf.get('dist', {})
            print(f"\n  🎯 Distribution Data:")
            for key, value in dist.items():
                print(f"    {key}: {value}")
                
                # If plus_100 is a dict, examine it in detail
                if key == 'plus_100' and isinstance(value, dict):
                    print(f"      Plus 100 breakdown:")
                    for score_key, score_value in value.items():
                        print(f"        {score_key}: {score_value}")
            
            print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    examine_dist_structure("688e66b6f4fc02e124e759c8")