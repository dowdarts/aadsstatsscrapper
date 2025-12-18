"""
Analyze the DartConnect event listing page structure
"""
import requests
from bs4 import BeautifulSoup
import json
import html as html_module

url = "https://tv.dartconnect.com/event/mt_joe6163l_1/matches"
print(f"Fetching event page: {url}\n")

response = requests.get(url)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.text)}\n")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check for Inertia.js data (similar to recap pages)
    app_div = soup.find('div', {'id': 'app'})
    if app_div and app_div.has_attr('data-page'):
        print("✅ Found Inertia.js data-page attribute")
        
        page_data_encoded = app_div['data-page']
        page_data = html_module.unescape(page_data_encoded)
        data = json.loads(page_data)
        
        print(f"Top-level keys: {list(data.keys())}")
        
        if 'props' in data:
            props = data['props']
            print(f"Props keys: {list(props.keys())}\n")
            
            # Look for match data
            for key in props.keys():
                if 'match' in key.lower():
                    print(f"Found match-related key: {key}")
                    matches_data = props[key]
                    print(f"  Type: {type(matches_data)}")
                    if isinstance(matches_data, dict):
                        print(f"  Keys: {list(matches_data.keys())}")
                    elif isinstance(matches_data, list):
                        print(f"  Length: {len(matches_data)}")
                        if matches_data:
                            print(f"  First item keys: {list(matches_data[0].keys()) if isinstance(matches_data[0], dict) else 'Not a dict'}")
                            print(f"\n  Sample match:")
                            print(json.dumps(matches_data[0], indent=4)[:500])
            
            # Save full props for inspection
            with open('event_props.json', 'w') as f:
                json.dump(props, f, indent=2)
            print(f"\n📄 Saved event_props.json for full inspection")
    else:
        print("❌ No Inertia.js data found")
        
        # Check for regular HTML links
        links = soup.find_all('a', href=True)
        match_links = [link['href'] for link in links if 'recap.dartconnect.com/matches' in link['href'] or '/matches/' in link['href']]
        
        if match_links:
            print(f"\n✅ Found {len(match_links)} match links in HTML:")
            for i, link in enumerate(match_links[:5], 1):
                print(f"  {i}. {link}")
        else:
            print("\n❌ No match links found in HTML")
else:
    print(f"❌ Failed to fetch page: {response.status_code}")
