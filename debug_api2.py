import json
from urllib.request import Request, urlopen

event_id = "mt_joe6163l_1"
api_url = f"https://tv.dartconnect.com/api2/event/{event_id}/matches"

print(f"Fetching: {api_url}")

request = Request(api_url, method='POST')
request.add_header('Content-Type', 'application/json')
request.add_header('User-Agent', 'Mozilla/5.0')

with urlopen(request, timeout=30) as response:
    data = json.loads(response.read().decode())

print(json.dumps(data, indent=2))
