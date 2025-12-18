"""
Analyze DartConnect page to find embedded match data
"""
import requests
import re
import json

# Fetch the page
url = "https://recap.dartconnect.com/matches/688e00ccf4fc02e124e7131c"
response = requests.get(url)
html = response.text

print(f"Status: {response.status_code}")
print(f"Content length: {len(html)}")

# Look for Inertia.js data
# The page uses Inertia.js which embeds data in a div with id="app"
pattern = r'"props":\s*({[^}]+(?:{[^}]+}[^}]*)*})'
matches = re.findall(pattern, html)

if matches:
    print(f"\nFound {len(matches)} potential data blocks")
    for i, match_text in enumerate(matches[:1]):  # Just show first one
        try:
            # Try to parse as JSON
            print(f"\n=== Data block {i+1} (first 1000 chars) ===")
            print(match_text[:1000])
        except Exception as e:
            print(f"Error: {e}")
else:
    print("\nNo props data found with basic pattern")
    # Try broader search
    if "props" in html:
        print("\n'props' keyword found in HTML, searching context...")
        idx = html.find('props')
        if idx != -1:
            print(f"\nContext around 'props' (500 chars):")
            print(html[max(0, idx-100):idx+400])
            
# Try to find data-page attribute which Inertia uses
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')
app_div = soup.find('div', {'id': 'app'})
if app_div and app_div.has_attr('data-page'):
    print("\n=== Found Inertia data in #app div ===")
    page_data = app_div['data-page']
    try:
        data = json.loads(page_data)
        print(f"Keys: {list(data.keys())}")
        if 'props' in data:
            props = data['props']
            print(f"\nProps keys: {list(props.keys())}")
            
            # Extract match info
            if 'matchInfo' in props:
                print("\n=== MATCH INFO ===")
                match_info = props['matchInfo']
                for key, value in match_info.items():
                    print(f"  {key}: {value}")
            
            # Extract home players
            if 'homePlayers' in props:
                print("\n=== HOME PLAYERS ===")
                for player in props['homePlayers']:
                    print(f"  {player}")
                    
            # Extract away players
            if 'awayPlayers' in props:
                print("\n=== AWAY PLAYERS ===")
                for player in props['awayPlayers']:
                    print(f"  {player}")
            
            # Extract segments (contains leg-by-leg data)
            if 'segments' in props:
                print("\n=== SEGMENTS (First segment only) ===")
                segments = props['segments']
                print(f"  Segment structure: {type(segments)}")
                if segments:
                    first_key = list(segments.keys())[0]
                    print(f"  First key: '{first_key}'")
                    first_segment = segments[first_key]
                    print(f"  First segment has {len(first_segment)} sets")
                    if first_segment and len(first_segment) > 0:
                        first_set = first_segment[0]
                        print(f"\n  First set data:")
                        for key, value in first_set.items():
                            if key != 'legs':  # Don't print all legs yet
                                print(f"    {key}: {value}")
                        
                        # Check if there are legs
                        if 'legs' in first_set:
                            print(f"\n  Number of legs: {len(first_set['legs'])}")
                            if first_set['legs']:
                                print(f"\n  First leg sample:")
                                first_leg = first_set['legs'][0]
                                print(f"    {json.dumps(first_leg, indent=6)}")
                
    except Exception as e:
        print(f"Error parsing data: {e}")
        import traceback
        traceback.print_exc()
    except:
        print(f"Data length: {len(page_data)}")
        print(f"First 500 chars: {page_data[:500]}")
