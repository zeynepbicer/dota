import json
import os
import time
from tempfile import gettempdir
from typing import List, Optional, Dict, Tuple, Callable

import requests

__all__ = ["get_dota_dataset"]


API_KEY = '76b70d83-68ce-4cde-b6ca-8425dd4876e4'

ApiKey = str
MatchId = str
GameMode = int
LobbyType = int
Seconds = int
JobId = int


class ParsedMatchCannotBeRetrievedError(Exception):
    pass


def _get_dota_public_match_info(api_key: ApiKey, less_than_match_id: Optional[MatchId] = None):
    if less_than_match_id is None:
        return requests.get(f'https://api.opendota.com/api/publicMatches?api_key={api_key}')
    return requests.get(
                f'https://api.opendota.com/api/publicMatches?less_than_match_id={less_than_match_id}&api_key={api_key}')


def _submit_parse_request_for_match(api_key: ApiKey, match_id: MatchId) -> JobId:
    response = requests.post(f'https://api.opendota.com/api/request/{match_id}?api_key={api_key}')
    if response.status_code != 200:
        raise ParsedMatchCannotBeRetrievedError(f"For match id {match_id}")
    return response.json()['job']['jobId']


def _is_parse_request_ready(job_id: JobId, api_key: Optional[ApiKey] = API_KEY) -> bool:
    response = requests.get(f'https://api.opendota.com/api/request/{job_id}?api_key={api_key}')
    if response.status_code != 200:
        raise ValueError(f"Cannot retrieve parse request status for job id {job_id}")
    return response.text == "null"


def _get_parsed_match(match_id: MatchId, api_key: Optional[ApiKey] = API_KEY) -> Dict:
    response = requests.get(f"https://api.opendota.com/api/matches/{match_id}?api_key={api_key}")
    if response.status_code != 200:
        raise ValueError(f"Cannot retrieve parsed match for job id {job_id}")
    return response.json()


def _default_on_error(request):
    print(request)


def _request_public_matches(data_size: int, api_key: ApiKey,
                            on_error: Optional[Callable] = _default_on_error) -> Tuple[List[Dict], int]:
    matches_json: List[Dict] = []
    tmp_ids: List[MatchId] = []
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


def _filter_match_ids(matches: List[Dict], game_mode: GameMode, lobby_types: List[LobbyType],
                      minimum_match_duration: Seconds) -> List[MatchId]:
    match_ids: List[MatchId] = []
    for match in matches:
        if match['game_mode'] == game_mode and \
                match['lobby_type'] in lobby_types and \
                match['duration'] > minimum_match_duration:
            match_ids.append(match['match_id'])
    return match_ids


def _submit_parse_request_for_matches(match_ids: List[MatchId], api_key: Optional[ApiKey] = API_KEY
                                      ) -> Dict[JobId, MatchId]:
    parsing_job_id_to_match_id: Dict[JobId, MatchId] = dict()
    for mid in match_ids:
        try:
            parsing_job_id_to_match_id[_submit_parse_request_for_match(api_key=api_key, match_id=mid)] = mid
        except ParsedMatchCannotBeRetrievedError:
            continue
    return parsing_job_id_to_match_id


def _get_parsed_data(parsing_job_id_to_match_id: Dict[JobId, MatchId],
                     api_key: Optional[ApiKey] = API_KEY) -> List[Dict]:
    parsed_data: List[Dict] = []
    available_job_ids = list(parsing_job_id_to_match_id.keys())
    while len(available_job_ids) > 0:
        for job_id in available_job_ids:
            if _is_parse_request_ready(job_id=job_id, api_key=api_key):
                try:
                    parsed_data.append(_get_parsed_match(match_id=parsing_job_id_to_match_id[job_id], api_key=api_key))
                except ValueError:
                    continue
                available_job_ids.pop(job_id)
    return parsed_data


def export_parsed_data(parsed_data: List[Dict], path_to_file: Optional[str] = None):
    if path_to_file is None:
        path_to_file = os.path.join(gettempdir(), "dota_dataset.json")
    with open(path_to_file, "w") as handle:
        json.dump(parsed_data, handle)


def get_dota_dataset(data_size: int, game_mode: GameMode, lobby_types: List[LobbyType],
                     minimum_match_duration: Seconds, api_key: Optional[ApiKey] = API_KEY,
                     path_to_output_file: Optional[str] = None):
    matches, number_of_errors = _request_public_matches(data_size=data_size, api_key=API_KEY)
    filtered_match_ids = _filter_match_ids(matches=matches, game_mode=game_mode, lobby_types=lobby_types, 
                                           minimum_match_duration=minimum_match_duration)
    parsing_job_id_to_match_id: Dict[JobId, MatchId] = _submit_parse_request_for_matches(
        match_ids=filtered_match_ids, api_key=api_key)
    parsed_data: List[Dict] = _get_parsed_data(parsing_job_id_to_match_id=parsing_job_id_to_match_id, api_key=api_key)
    export_parsed_data(parsed_data=parsed_data, path_to_file=path_to_output_file)


if __name__ == "__main__":
    start_time = time.time()
    get_dota_dataset(data_size=50, game_mode=22, lobby_types=[5, 6, 7], minimum_match_duration=900, api_key=API_KEY)
    print(f'Finished in {time.time() - start_time} seconds')
