import json
from urllib.request import Request, urlopen

event_id = "mt_joe6163l_1"
api_url = f"https://tv.dartconnect.com/api2/event/{event_id}/matches"

request_obj = Request(api_url, method='POST')
request_obj.add_header('Content-Type', 'application/json')
request_obj.add_header('User-Agent', 'Mozilla/5.0')

with urlopen(request_obj, timeout=30) as response:
    result = json.loads(response.read().decode())

print("Keys in response:", result.keys())
print("\nFull response structure:")
print(json.dumps(result, indent=2)[:2000])
