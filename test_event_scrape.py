#!/usr/bin/env python3
"""
Test event batch scraping with real AADS event URL
"""

import requests
import json

def test_event_scrape():
    # Your actual event URL
    event_url = "https://tv.dartconnect.com/event/mt_joe6163l_1/matches"
    
    print(f"Testing event batch scrape with: {event_url}")
    print("=" * 70)
    
    # Send request to Flask API
    api_url = "http://localhost:5000/api/scrape-event"
    payload = {"event_url": event_url}
    
    try:
        response = requests.post(api_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Event scrape successful!")
            print(f"Total matches found: {result.get('total_matches', 0)}")
            print(f"Successfully scraped: {result.get('successful_scrapes', 0)}")
            print(f"Failed scrapes: {result.get('failed_scrapes', 0)}")
            
            if 'match_urls' in result:
                print(f"\nMatch URLs found ({len(result['match_urls'])}):")
                for i, url in enumerate(result['match_urls'][:5], 1):  # Show first 5
                    print(f"  {i}. {url}")
                if len(result['match_urls']) > 5:
                    print(f"  ... and {len(result['match_urls']) - 5} more")
            
            if 'players_updated' in result:
                print(f"\nPlayers updated: {len(result['players_updated'])}")
                for player in result['players_updated'][:3]:  # Show first 3
                    print(f"  - {player}")
                if len(result['players_updated']) > 3:
                    print(f"  ... and {len(result['players_updated']) - 3} more")
                    
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_event_scrape()