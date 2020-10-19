import json
import requests
with open('match_details.json') as f:
    data = json.load(f)

names = {}
with open('heroes.json') as f:
    heroes = json.load(f)
    for h in heroes:
        names[h['id']] = h['localized_name']

for pick in data[0]['picks_bans']:
    if pick['is_pick']:
        print(names[pick['hero_id']])
print(data[0]['match_id'])
for player in data[0]['players']:
    print(player['gold_per_min'], names[player['hero_id']])



