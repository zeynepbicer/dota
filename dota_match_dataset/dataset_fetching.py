import json
import os
import time
from tempfile import gettempdir
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, wait

from dota_match_dataset.type_hints import *
from dota_match_dataset.open_dota_interface import *
from dota_match_dataset.logger_config import get_logger


__all__ = ["fetch_dota_dataset_serial", "fetch_dota_dataset_concurrent"]

_logger = get_logger()


def _fetch_public_matches(open_dota_api: OpenDotaApi, minimum_number_of_matches: int,
                          game_mode: GameMode, lobby_types: List[LobbyType],
                          minimum_match_duration: Seconds, retries: int = 5) -> List[Dict]:
    fetched_matches: List[Dict] = []
    number_of_retrieved_matches = 0
    number_of_retries = 0
    minimum_retrieved_match_id: Optional[MatchId] = None

    while number_of_retrieved_matches <= minimum_number_of_matches:
        try:
            matches = open_dota_api.get_random_public_match_info(less_than_match_id=minimum_retrieved_match_id)
            matches = _filter_matches(matches=matches, game_mode=game_mode, lobby_types=lobby_types,
                                      minimum_match_duration=minimum_match_duration)
            fetched_matches += matches
            number_of_retrieved_matches += len(matches)
            minimum_retrieved_match_id = min([_match['match_id'] for _match in matches])
            time.sleep(0.1)

        except PublicMatchInfoCannotBeRetrievedError as e:
            number_of_retries += 1
            if number_of_retries > retries:
                raise PublicMatchInfoCannotBeRetrievedError(f"Failed to fetch match info with {retries} retries") from e

    _logger.info(f"Fetched {len(fetched_matches)} public match info")
    return fetched_matches


def _filter_matches(matches: List[Dict], game_mode: GameMode, lobby_types: List[LobbyType],
                    minimum_match_duration: Seconds) -> List[Dict]:
    filtered_matches: List[Dict] = []
    for match in matches:
        if match['game_mode'] == game_mode and \
                match['lobby_type'] in lobby_types and \
                match['duration'] > minimum_match_duration:
            filtered_matches.append(match)
    return filtered_matches


def _submit_parse_request_for_matches(open_dota_api: OpenDotaApi, match_ids: List[MatchId]) -> Dict[JobId, MatchId]:
    parsing_job_id_to_match_id: Dict[JobId, MatchId] = dict()
    for mid in match_ids:
        try:
            parsing_job_id_to_match_id[open_dota_api.submit_parse_request_for_match(match_id=mid)] = mid
            _logger.info(f"Submitted parse request for match [{mid}]")
        except ParsedRequestCannotBeSubmittedError:
            continue
    return parsing_job_id_to_match_id


def _get_parsed_data(open_dota_api: OpenDotaApi, parsing_job_id_to_match_id: Dict[JobId, MatchId]) -> List[Dict]:
    parsed_data: List[Dict] = []
    available_job_ids = list(parsing_job_id_to_match_id.keys())
    while len(available_job_ids) > 0:
        for i, job_id in enumerate(available_job_ids):
            if open_dota_api.is_parse_request_ready(job_id=job_id):
                try:
                    parsed_data.append(open_dota_api.get_parsed_match(match_id=parsing_job_id_to_match_id[job_id]))
                    _logger.debug(f"Fetched the parsed match data for [{parsing_job_id_to_match_id[job_id]}]")
                except ParsedMatchCannotBeRetrievedError:
                    continue
                available_job_ids.pop(i)
    return parsed_data


def _export_parsed_data(parsed_data: List[Dict], path_to_file: Optional[str] = None):
    if path_to_file is None:
        path_to_file = os.path.join(gettempdir(), "dota_dataset.json")
    with open(path_to_file, "w") as handle:
        json.dump(parsed_data, handle, indent=2)
    _logger.info(f"Exported dataset to {path_to_file}")


def fetch_dota_dataset_serial(open_dota_api: OpenDotaApi, minimum_number_of_matches: int, game_mode: GameMode,
                              lobby_types: List[LobbyType], minimum_match_duration: Seconds,
                              path_to_output_file: Optional[str] = None,
                              maximum_number_of_matches: Optional[int] = None):
    matches = _fetch_public_matches(
        open_dota_api=open_dota_api, minimum_number_of_matches=minimum_number_of_matches, game_mode=game_mode,
        lobby_types=lobby_types, minimum_match_duration=minimum_match_duration
    )
    if maximum_number_of_matches is not None:
        matches = matches[:maximum_number_of_matches]

    parsing_job_id_to_match_id: Dict[JobId, MatchId] = _submit_parse_request_for_matches(
        match_ids=[m["match_id"] for m in matches], open_dota_api=open_dota_api)
    parsed_data: List[Dict] = _get_parsed_data(parsing_job_id_to_match_id=parsing_job_id_to_match_id,
                                               open_dota_api=open_dota_api)
    _export_parsed_data(parsed_data=parsed_data, path_to_file=path_to_output_file)


def fetch_dota_dataset_concurrent(open_dota_api: OpenDotaApi, minimum_number_of_matches: int, game_mode: GameMode,
                                  lobby_types: List[LobbyType], minimum_match_duration: Seconds,
                                  path_to_output_file: Optional[str] = None,
                                  maximum_number_of_matches: Optional[int] = None):
    matches = _fetch_public_matches(
        open_dota_api=open_dota_api, minimum_number_of_matches=minimum_number_of_matches, game_mode=game_mode,
        lobby_types=lobby_types, minimum_match_duration=minimum_match_duration
    )
    if maximum_number_of_matches is not None:
        matches = matches[:maximum_number_of_matches]

    executor = ThreadPoolExecutor(max_workers=20)
    futures = [executor.submit(open_dota_api.submit_parse_request_for_match, m["match_id"]) for m in matches]
    wait(futures)

    parsing_job_id_to_match_id = {}
    for match, future in zip(matches, futures):
        try:
            parsing_job_id_to_match_id[future.result()] = match["match_id"]
        except Exception as e:
            _logger.error(f"Failed to fetch results for future (match_id = {match['match_id']}): {e}")

    parsed_data: List[Dict] = _get_parsed_data(parsing_job_id_to_match_id=parsing_job_id_to_match_id,
                                               open_dota_api=open_dota_api)
    _export_parsed_data(parsed_data=parsed_data, path_to_file=path_to_output_file)
