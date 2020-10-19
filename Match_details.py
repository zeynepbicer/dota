import json
import requests
import time
api_key = '76b70d83-68ce-4cde-b6ca-8425dd4876e4'

with open('parsed_matches.json') as f:
    match_ids = json.load(f)

error = 0
match_details = []
to_be_parsed = []
for match_id in match_ids:
    try:
        r = requests.get(f'https://api.opendota.com/api/matches/{match_id}?api_key={api_key}')
        match = r.json()
        if match['radiant_gold_adv'] is None:
            print('To be investigated')
            to_be_parsed.append(match_id)
        else:
            match_details.append(match)
            print(f'Requesting match detail for {match_id}... {match_ids.index(match_id)+1}/{len(match_ids)}')
        time.sleep(r.elapsed.total_seconds())
    except:
        error += 1
        continue
print(f'Success: {len(match_details)}, Fail: {len(to_be_parsed)}, Error: {error}')
with open('match_details.json', 'w') as f:
    json.dump(match_details, f, indent=2)
with open('not_parsed_ids.json', 'w') as f:
    json.dump(to_be_parsed, f)