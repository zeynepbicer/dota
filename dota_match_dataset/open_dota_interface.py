from typing import Optional, Dict, List

import requests

from dota_match_dataset.type_hints import ApiKey, MatchId, JobId

__all__ = [
    "PublicMatchInfoCannotBeRetrievedError", "ParsedMatchCannotBeRetrievedError",

    "get_dota_public_match_info", "submit_parse_request_for_match", "is_parse_request_ready", "get_parsed_match"
]


class PublicMatchInfoCannotBeRetrievedError(Exception):
    pass


class ParsedMatchCannotBeRetrievedError(Exception):
    pass


def get_dota_public_match_info(api_key: ApiKey, less_than_match_id: Optional[MatchId] = None) -> List[Dict]:
    if less_than_match_id is None:
        response = requests.get(f'https://api.opendota.com/api/publicMatches?api_key={api_key}')
    else:
        response = requests.get(
            f'https://api.opendota.com/api/publicMatches?less_than_match_id={less_than_match_id}&api_key={api_key}')
    if response.status_code != 200:
        raise PublicMatchInfoCannotBeRetrievedError("")
    return response.json()


def submit_parse_request_for_match(api_key: ApiKey, match_id: MatchId) -> JobId:
    response = requests.post(f'https://api.opendota.com/api/request/{match_id}?api_key={api_key}')
    if response.status_code != 200:
        raise ParsedMatchCannotBeRetrievedError(f"For match id {match_id}")
    return response.json()['job']['jobId']


def is_parse_request_ready(job_id: JobId, api_key: ApiKey) -> bool:
    response = requests.get(f'https://api.opendota.com/api/request/{job_id}?api_key={api_key}')
    if response.status_code != 200:
        raise ValueError(f"Cannot retrieve parse request status for job id {job_id}")
    return response.text == "null"


def get_parsed_match(match_id: MatchId, api_key: ApiKey) -> Dict:
    response = requests.get(f"https://api.opendota.com/api/matches/{match_id}?api_key={api_key}")
    if response.status_code != 200:
        raise ValueError(f"Cannot retrieve parsed match for match id {match_id}")
    return response.json()
