"""
Fetch all matches from the event via DartConnect API
"""
import requests
import json

# Event ID from the URL: mt_joe6163l_1
event_id = "mt_joe6163l_1"

# Try the API2 endpoint that was in the routes
api_url = f"https://tv.dartconnect.com/api2/event/{event_id}/matches"

print(f"Fetching matches from API: {api_url}\n")

response = requests.get(api_url)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    try:
        data = response.json()
        print(f"Response type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            
            # Look for matches in the response
            for key in data.keys():
                if 'match' in key.lower():
                    matches = data[key]
                    print(f"\nFound '{key}': {type(matches)}")
                    if isinstance(matches, list):
                        print(f"  Number of matches: {len(matches)}")
                        if matches:
                            print(f"\n  Sample match:")
                            sample = matches[0]
                            print(f"    Keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not a dict'}")
                            if isinstance(sample, dict):
                                # Look for match ID or URL
                                for k, v in sample.items():
                                    if 'id' in k.lower() or 'url' in k.lower() or 'match' in k.lower():
                                        print(f"    {k}: {v}")
        elif isinstance(data, list):
            print(f"Response is a list with {len(data)} items")
            if data:
                print(f"\nFirst item:")
                print(json.dumps(data[0], indent=2)[:800])
        
        # Save full response
        with open('matches_api_response.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n📄 Saved matches_api_response.json")
        
    except json.JSONDecodeError:
        print("Response is not JSON")
        print(response.text[:500])
else:
    print(f"Failed to fetch: {response.status_code}")
    print(response.text[:500])
