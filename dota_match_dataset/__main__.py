import os
import time

from dota_match_dataset import fetch_dota_dataset_concurrent, OpenDotaApi

__all__ = ["main"]


def main():
    start_time = time.time()
    fetch_dota_dataset_concurrent(open_dota_api=OpenDotaApi(os.getenv("OPEN_DOTA_API_KEY")),
                                  minimum_number_of_matches=1000, game_mode=22, lobby_types=[5, 6, 7],
                                  minimum_match_duration=900, maximum_number_of_matches=1100,
                                  path_to_output_file="/tmp/dota-dataset.json")
    print(f'Finished in {time.time() - start_time} seconds')


main()
