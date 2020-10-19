import os
import time

from dota_match_dataset import fetch_dota_dataset

__all__ = ["main"]


def main():
    start_time = time.time()
    fetch_dota_dataset(api_key=os.getenv("OPEN_DOTA_API_KEY"), minimum_number_of_matches=2, game_mode=22,
                       lobby_types=[5, 6, 7], minimum_match_duration=900, maximum_number_of_matches=5,
                       path_to_output_file="/tmp/dota-dataset.json")
    print(f'Finished in {time.time() - start_time} seconds')


main()
