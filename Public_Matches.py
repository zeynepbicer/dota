import json
import time
from typing import List, Optional, Dict, Tuple, Callable

import requests

__all__ = ["get_dota_dataset"]


API_KEY = '76b70d83-68ce-4cde-b6ca-8425dd4876e4'

ApiKey = str
ObjectId = str
GameMode = int
LobbyType = int
Seconds = int


class ParsedMatchCannotBeRetrievedError(Exception):
    pass


def _get_dota_public_match_info(api_key: ApiKey, less_than_match_id: Optional[ObjectId] = None):
    if less_than_match_id is None:
        return requests.get(f'https://api.opendota.com/api/publicMatches?api_key={api_key}')
    return requests.get(
                f'https://api.opendota.com/api/publicMatches?less_than_match_id={less_than_match_id}&api_key={api_key}')


def _get_parsed_match(api_key: ApiKey, match_id: ObjectId) -> Dict:
    response = requests.post(f'https://api.opendota.com/api/request/{match_id}?api_key={api_key}')
    if response.status_code != 200:
        raise ParsedMatchCannotBeRetrievedError(f"For match id {match_id}")
    return response.json()


def _default_on_error(request):
    print(request)


def _request_public_matches(data_size: int, api_key: ApiKey,
                            on_error: Optional[Callable] = _default_on_error) -> Tuple[List[Dict], int]:
    matches_json: List[Dict] = []
    tmp_ids: List[ObjectId] = []
    number_of_failures = 0

    first_response = _get_dota_public_match_info(api_key=api_key)
    minimum_retrieved_match_id = first_response.json()["match_id"]

    for i in range(data_size - 1):
        response = _get_dota_public_match_info(api_key=api_key, less_than_match_id=minimum_retrieved_match_id)
        if response.status_code != 200:
            on_error(response)
            number_of_failures += 1
        else:
            tmp_ids.clear()
            matches = response.json()
            tmp_ids += [_match['match_id'] for _match in matches]
            minimum_retrieved_match_id = min(tmp_ids)
            matches_json += matches
            time.sleep(min(response.elapsed.total_seconds(), 2))
    return matches_json, number_of_failures


def get_dota_dataset(data_size: int, game_mode: GameMode, lobby_types: List[LobbyType],
                     minimum_match_duration: Seconds, api_key: Optional[ApiKey] = API_KEY) -> :
    t1 = time.time()
    match_ids: List[ObjectId] = []
    matches, number_of_errors = _request_public_matches(data_size=data_size, api_key=API_KEY)

    for match in matches:
        if match['game_mode'] == game_mode and \
                match['lobby_type'] in lobby_types and \
                match['duration'] > minimum_match_duration:
            match_ids.append(match['match_id'])

    print(f'Got {len(match_ids)} match id\'s ranked all pick matches with {number_of_errors} errors')

    job_ids = dict()
    parsed_match_ids: List[ObjectId] = []
    for i, m_id in enumerate(match_ids):
        try:
            parsed_match = _get_parsed_match(api_key=api_key, match_id=m_id)
            job_ids[m_id] = parsed_match['job']['jobId']
            parsed_match_ids.append(m_id)
            print(f'Requesting parse for match id {m_id}...  {i + 1}/{len(match_ids)}')
            time.sleep(1)
        except ParsedMatchCannotBeRetrievedError:
            continue

    with open('parsed_matches.json', 'w') as f:
        json.dump(parsed_match_ids, f)
    t2 = time.time()
    print(f'Finished in {t2 - t1} seconds')


if __name__ == "__main__":
    get_dota_dataset(50)

