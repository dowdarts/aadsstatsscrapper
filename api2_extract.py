#!/usr/bin/env python3
"""
Extract match URLs from the api2 response structure we discovered
"""
import json

def extract_from_api2():
    """Extract match URLs from api2 response"""
    print("🔍 Extracting match URLs from api2 response...")
    print("=" * 60)
    
    try:
        with open('api2_matches_response.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ api2_matches_response.json not found")
        return []
    
    match_urls = []
    
    if 'payload' in data:
        payload = data['payload']
        print(f"📋 Payload sections: {list(payload.keys())}")
        
        for section_name, matches in payload.items():
            if isinstance(matches, list) and len(matches) > 0:
                print(f"\n📂 Section '{section_name}': {len(matches)} matches")
                
                for i, match in enumerate(matches):
                    if isinstance(match, dict) and 'mi' in match:
                        match_id = match['mi']
                        
                        # Try different URL formats
                        urls_to_try = [
                            f"https://tv.dartconnect.com/match/{match_id}",
                            f"https://recap.dartconnect.com/matches/{match_id}",
                        ]
                        
                        # Get match info
                        home_player = match.get('hc', 'Unknown')
                        away_player = match.get('ac', 'Unknown') 
                        score = match.get('ms', 'No score')
                        event_label = match.get('el', 'Unknown event')
                        
                        print(f"   Match {i+1}: {home_player} vs {away_player} ({score})")
                        print(f"      Event: {event_label}")
                        print(f"      Match ID: {match_id}")
                        
                        # Add the tv.dartconnect.com URL to our list
                        tv_url = f"https://tv.dartconnect.com/match/{match_id}"
                        match_urls.append(tv_url)
                        print(f"      URL: {tv_url}")
    
    print(f"\n📊 Total match URLs extracted: {len(match_urls)}")
    
    if match_urls:
        # Save to file
        with open('api2_match_urls.txt', 'w') as f:
            for url in match_urls:
                f.write(url + '\n')
        print(f"📁 URLs saved to api2_match_urls.txt")
        
        print("\n🎯 Event scraper should now work with these URLs!")
        print("   These URLs can be used by your Edge Function for batch processing")
        
        return match_urls
    else:
        print("❌ No matches found")
        return []

if __name__ == "__main__":
    extract_from_api2()