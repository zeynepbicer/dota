# Dota 2 Match Data using OpenDota API

Get match data for a large amount of randomly selected matches. Can be used for predictive analysis.

## What do you need?

You need an API key from OpenDota, it doesn't cost much! The code does not work without an API key as OpenDota does not 
support the number of calls needed for the size of the dataset for free.

Once you have the API key, just replace the placeholder

`api_key = "API_KEY_HERE"`

## How to customise it?

```
minimum_number_of_matches = 1000
game_mode=22
lobby_types=[5, 6, 7]
minimum_match_duration=900
```

The code is configured to get All Pick matches `game mode = 22` and lobby types Ranked, Normal, Party All Pick
`lobby_types=[5, 6, 7]`.

The minimum match duration is set to 15 minutes (900 seconds) as matches that end before 15 minutes can be outlier values
for further analysis.

`minimum_number_of_matches = 1000` You can increase/decrease this value depending on how many matches you need.

##Good Luck~