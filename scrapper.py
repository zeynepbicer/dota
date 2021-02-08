import requests
import json
import dask
from dask.diagnostics import ProgressBar


base_url = "https://api.opendota.com/api"
api_key = "API_KEY"

minimum_number_of_matches = 1000
game_mode=22
lobby_types=[5, 6, 7]
minimum_match_duration=900


pbar = ProgressBar()


def post_jobs(match):
    pst = requests.post(f'{base_url}/request/{match["match_id"]}?api_key={api_key}')
    return pst.json()['job']['jobId']


def get_matches(match):
    response = requests.get(f"{base_url}/matches/{match['match_id']}")
    return response.json()


print('Initiate Public Matches GET requests.')
matches = []

first_response =  requests.get(f'{base_url}/publicMatches?api_key={api_key}').json()
filtered = [r for r in first_response if r['game_mode'] == game_mode and r['lobby_type'] in lobby_types and r['duration'] > minimum_match_duration]
matches += filtered

tmp_ids = [r['match_id'] for r in first_response]

min_id = min(tmp_ids)

while len(matches) <= minimum_number_of_matches:
    resp = requests.get(f'{base_url}/publicMatches?api_key={api_key}&less_than_match_id={min_id}').json()
    filtered = [r for r in resp if r['game_mode'] == game_mode and r['lobby_type'] in lobby_types and r['duration'] > minimum_match_duration]
    matches += filtered
    tmp_ids = [r['match_id'] for r in resp]
    min_id = min(tmp_ids)

print(f"Got {len(matches)} match IDs.")

print("Submitting POST requests.")
job_ids = [dask.delayed(post_jobs)(m) for m in matches]

pbar.register()
job_ids = list(dask.compute(*job_ids))
print("Done submitting POST requests.")

print('Waiting for Jobs to finish.')

while job_ids:
    for i, job in enumerate(job_ids):
        resp = requests.get(f'{base_url}/request/{job}?api_key={api_key}')
        if resp.text == 'null':
            del job_ids[i]

print(f'All Job requests are finished.')

print(f'Requesting data for {len(matches)} matches.')

match_details = [dask.delayed(get_matches)(match) for match in matches]
    
pbar.register()
match_details = list(dask.compute(*match_details))

print('Finished requesting match data.')

with open('match_details.json', 'w') as f:
    json.dump(match_details, f, indent = 2)

print('Done')



