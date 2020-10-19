from typing import Optional, Dict, List

import requests

from dota_match_dataset.type_hints import ApiKey, MatchId, JobId

__all__ = [
    "PublicMatchInfoCannotBeRetrievedError", "ParsedRequestCannotBeSubmittedError",
    "ParseRequestStatusCannotBeRetrievedError", "ParsedMatchCannotBeRetrievedError",

    "OpenDotaApi"
]


class PublicMatchInfoCannotBeRetrievedError(Exception):
    pass


class ParsedRequestCannotBeSubmittedError(Exception):
    pass


class ParseRequestStatusCannotBeRetrievedError(Exception):
    pass


class ParsedMatchCannotBeRetrievedError(Exception):
    pass


def _check_status(response, exception, *args):
    if response.status_code != 200:
        raise exception(*args)


class OpenDotaApi:
    _base_url = "https://api.opendota.com/api"
    
    def __init__(self, api_key: ApiKey):
        self._api_key = api_key

    def get_random_public_match_info(self, less_than_match_id: Optional[MatchId] = None) -> List[Dict]:
        _path = f'{self._base_url}/publicMatches?api_key={self._api_key}'
        if less_than_match_id is not None:
            _path += f'&less_than_match_id={less_than_match_id}'
        response = requests.get(_path)
        _check_status(response, PublicMatchInfoCannotBeRetrievedError, "")
        return response.json()
    
    def submit_parse_request_for_match(self, match_id: MatchId) -> JobId:
        response = requests.post(f'{self._base_url}/request/{match_id}?api_key={self._api_key}')
        _check_status(response, ParsedRequestCannotBeSubmittedError, f"For match id {match_id}")
        return response.json()['job']['jobId']
    
    def is_parse_request_ready(self, job_id: JobId) -> bool:
        response = requests.get(f'{self._base_url}/request/{job_id}?api_key={self._api_key}')
        _check_status(response, ParseRequestStatusCannotBeRetrievedError,
                      f"Cannot retrieve parse request status for job id {job_id}")
        return response.text == "null"
    
    def get_parsed_match(self, match_id: MatchId) -> Dict:
        response = requests.get(f"{self._base_url}/matches/{match_id}?api_key={self._api_key}")
        _check_status(response, ParsedMatchCannotBeRetrievedError,
                      f"Cannot retrieve parsed match for match id {match_id}")
        return response.json()
