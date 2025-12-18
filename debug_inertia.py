"""
Debug the Inertia.js parsing
"""
import requests
from bs4 import BeautifulSoup
import html
import json

url = "https://recap.dartconnect.com/matches/688e00ccf4fc02e124e7131c"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

print(f"Status: {response.status_code}")
print(f"Content length: {len(response.text)}")

# Find the app div
app_div = soup.find('div', {'id': 'app'})
if not app_div:
    print("❌ No #app div found")
    exit()

print("✅ Found #app div")

if not app_div.has_attr('data-page'):
    print("❌ #app div has no data-page attribute")
    print(f"   Attributes: {app_div.attrs.keys()}")
    exit()

print("✅ Found data-page attribute")

# Parse the JSON
page_data_encoded = app_div['data-page']
page_data = html.unescape(page_data_encoded)

try:
    data = json.loads(page_data)
    print(f"✅ Parsed JSON successfully")
    print(f"   Top-level keys: {list(data.keys())}")
    
    if 'props' in data:
        props = data['props']
        print(f"   Props keys: {list(props.keys())}")
        
        if 'segments' in props:
            segments = props['segments']
            print(f"\n✅ Found segments")
            print(f"   Segments type: {type(segments)}")
            print(f"   Segments keys: {list(segments.keys())}")
            
            # Check first segment
            if segments:
                first_key = list(segments.keys())[0]
                first_segment = segments[first_key]
                print(f"\n   First segment key: '{first_key}'")
                print(f"   First segment type: {type(first_segment)}")
                print(f"   First segment length: {len(first_segment)}")
                
                if first_segment and len(first_segment) > 0:
                    first_set = first_segment[0]
                    print(f"\n   First set type: {type(first_set)}")
                    
                    # If it's a list, it's probably a list of legs/sets
                    if isinstance(first_set, list):
                        print(f"   First set is a list with {len(first_set)} legs")
                        if first_set:
                            # Save the list for inspection
                            with open('legs_sample.json', 'w') as f:
                                json.dump(first_set, f, indent=2)
                            print(f"   📄 Saved legs_sample.json")
                            
                            actual_leg = first_set[0]
                            print(f"\n   First leg type: {type(actual_leg)}")
                            print(f"   First leg keys: {list(actual_leg.keys())}")
                            
                            # Check for home and away player data
                            if 'home' in actual_leg:
                                home = actual_leg['home']
                                print(f"\n   Home player data keys: {list(home.keys())}")
                                print(f"   Sample home data: {json.dumps(home, indent=4)[:300]}")
                            
                            if 'away' in actual_leg:
                                away = actual_leg['away']
                                print(f"\n   Away player data keys: {list(away.keys())}")
                                print(f"   Sample away data: {json.dumps(away, indent=4)[:300]}")
                    else:
                        print(f"   First set keys: {list(first_set.keys())}")
                    
                    if 'legs' in first_set:
                        legs = first_set['legs']
                        print(f"\n✅ Found legs")
                        print(f"   Number of legs: {len(legs)}")
                        
                        if legs:
                            first_leg = legs[0]
                            print(f"\n   First leg keys: {list(first_leg.keys())}")
                            
                            if 'home_player' in first_leg:
                                hp = first_leg['home_player']
                                print(f"\n   Home player data:")
                                print(f"     Keys: {list(hp.keys())}")
                                print(f"     Name: {hp.get('name', 'N/A')}")
                                print(f"     Darts thrown: {hp.get('darts_thrown', 'N/A')}")
                                print(f"     Score: {hp.get('score', 'N/A')}")
                                print(f"     Marks: {hp.get('marks', 'N/A')}")
                            
                            # Save full leg data for inspection
                            with open('first_leg_sample.json', 'w') as f:
                                json.dump(first_leg, f, indent=2)
                            print(f"\n📄 Saved first_leg_sample.json for inspection")
        else:
            print("❌ No 'segments' in props")
            
except json.JSONDecodeError as e:
    print(f"❌ JSON decode error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
