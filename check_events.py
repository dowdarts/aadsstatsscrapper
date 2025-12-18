import json

with open('event_props.json') as f:
    data = json.load(f)

events = data.get('tournamentEvents', [])
print(f'Tournament Events: {type(events)}')
print(f'Length: {len(events) if isinstance(events, list) else "Not a list"}')

if events:
    print('\nFirst event sample:')
    print(json.dumps(events[0], indent=2)[:1500])
