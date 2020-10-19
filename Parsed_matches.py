import json
import requests
import time

t1 = time.time()
API_KEY = '76b70d83-68ce-4cde-b6ca-8425dd4876e4'
with open('parsed_matches.json') as f:
    jobIds = json.load(f)
match_detail_json = []
errors = 0

while jobIds:
    for match_id, job_id in jobIds.items():
        r = requests.get(f'https://api.opendota.com/api/request/{job_id}?api_key={api_key}')
        print(f'Job status for {match_id} is {r.json()}')
        if r.text == 'null':
            r = requests.get(f"https://api.opendota.com/api/matches/{match_id}?api_key={api_key}")
            del jobIds[match_id]
            try:
                match_detail_json.append(r.json())
                time.sleep(r.elapsed.total_seconds())
            except TypeError:
                errors += 1
print(f'Got match details for {len(match_detail_json)} matches with {errors} errors')
with open('match_details.json', 'w') as f:
    json.dump(match_detail_json, f, indent=2)
t2 = time.time()
print(f'Finished in {t2 - t1} seconds')