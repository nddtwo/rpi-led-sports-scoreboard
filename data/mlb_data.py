from setup.session_setup import session
from datetime import datetime as dt
from datetime import timezone as tz


def get_games(date):
    """ Loads MLB game data for the provided date.

    Args:
        date (date): Date that game data should be pulled for.

    Returns:
        list: List of dicts of game data.
    """
    
    # Create an empty list to hold the game dicts.
    games = []

    # Build the URL for the MLB game API call.
    base_url = 'https://statsapi.mlb.com/api/v1/schedule/games/'
    url_params = {
        'sportId': 1,  # MLB sport ID
        'date': date.strftime('%Y-%m-%d'), # Format date as YYYY-MM-DD 
        'hydrate': [ # Hydrations add extra details to the API response.
            'team',
            'linescore'
        ],
        'fields': [ # Fields filter to limit API response to only the data we need.
            'totalGames',
            'dates',
            'games',
            'gamePk',
            'gameType',
            'gameDate',
            'status',
            'abstractGameState',
            'detailedState',
            'startTimeTBD',
            'linescore',
            'teams',
            'away',
            'team',
            'abbreviation',
            'home',
            'team',
            'abbreviation',
            'linescore',
            'currentInning',
            'inningState',
            'teams',
            'home',
            'runs',
            'away',
            'runs',
            'outs',
            'offense',
            'first',
            'second',
            'third'
        ]
    }
    url = base_url + '?' + '&'.join([f'{key}={",".join(value) if isinstance(value, list) else value}' for key, value in url_params.items()])
    
    # Call the MLB game API for the date specified and store the JSON results.
    games_response = session.get(url=url)
    games_json = games_response.json()['dates'][0]['games']

    # For each game, build a dict recording current game details.
    if games_json: # If games today.
        for game in games_json:
            games.append({
                'game_id': game['gamePk'],
                'home_abrv': game['teams']['home']['team']['abbreviation'],
                'away_abrv': game['teams']['away']['team']['abbreviation'],
                'home_score': game.get('linescore', {}).get('teams', {}).get('home', {}).get('runs', 0), # These won't exist until the game starts.
                'away_score': game.get('linescore', {}).get('teams', {}).get('away', {}).get('runs', 0),
                'start_datetime_utc': dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc),
                'start_datetime_local': dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None), # Convert UTC to local time.
                'status': game['status']['abstractGameState'],
                'detailed_status': game['status']['detailedState'],
                'has_started': True if game['status']['abstractGameState'] in ['Live', 'Final'] else False,
                'inning_num': game.get('linescore', {}).get('currentInning'), # These won't exist until the game starts.
                'inning_state': game.get('linescore', {}).get('inningState'),
                'outs': game.get('linescore', {}).get('outs', 0),
                'runner_on_first': True if 'first' in game.get('linescore', {}).get('offense', {}) else False,
                'runner_on_second': True if 'second' in game.get('linescore', {}).get('offense', {}) else False,
                'runner_on_third': True if 'third' in game.get('linescore', {}).get('offense', {}) else False,
                'home_team_scored': False,
                'away_team_scored': False,
                'scoring_team': None
            })

    # Sort games by start datetime and game ID to ensure consistent order. Start datetime needed since game IDs can have a weird order due to postponement, etc.
    games = sorted(games, key=lambda x: (x['start_datetime_utc'], x['game_id']))
            
    return games


def get_next_game(team):
    """ Loads next game details for the supplied MLB team.
    If the team is currently playing, will return details of the current game.

    Args:
        team (str): Team abbreviation to pull next game details for.

    Returns:
        dict: Dict of next game details.
    """

    # Note current datetime.
    cur_datetime = dt.today().astimezone()
    cur_date = cur_datetime.date()

    # Convert provided team abbreviation to team ID for the API call.
    team = determine_team_abbreviation(team)

    # Build the URL for the MLB game API call.
    base_url = 'https://statsapi.mlb.com/api/v1/teams/'
    url_params = {
        'teamId': team,
        'hydrate': [ # Hydrations add extra details to the API response.
            'nextSchedule(team)',
        ],
        'fields': [ # Fields filter to limit API response to only the data we need.
            'teams',
            'nextGameSchedule',
            'dates',
            'games',
            'gameDate',
            'status',
            'abstractGameState',
            'detailedState',
            'teams',
            'away',
            'team',
            'abbreviation'
        ]
    }
    url = base_url + '?' + '&'.join([f'{key}={",".join(value) if isinstance(value, list) else value}' for key, value in url_params.items()])
    
    # Call the MLB team API for the team specified (hydrated with next games details) and store the JSON results.
    games_response = session.get(url=url)
    all_schedule_json = games_response.json()['teams'][0]['nextGameSchedule']['dates']

    # Since an MLB team can play multiple games in a day, we'll need to flatten.
    schedule_json = []
    for game_date in all_schedule_json:
        for game in game_date['games']:
            schedule_json.append(game)

    # Determine the next game for the team specified and return game details.
    for game in schedule_json:
        if game['status']['abstractGameState'] in ['Preview', 'Live']:
            # Put together a dictionary with needed details.
            next_game = {
                'home_or_away': 'away' if game['teams']['home']['team']['abbreviation'] != team else 'home',
                'opponent_abrv': game['teams']['home']['team']['abbreviation'] if game['teams']['home']['team']['abbreviation'] != team else game['teams']['away']['team']['abbreviation'],
                'start_datetime_utc': dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc),
                'start_datetime_local': dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None),
                'is_today': True if dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None).date() == cur_date or dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None) < cur_datetime else False, # TODO: clean this up. Needed in case game is still going when date rolls over.
                'has_started': True if cur_datetime >= dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None) else False
            }
            return(next_game)
    
    # If no next game found, return None.
    return None


def get_standings():
    """ Loads current MLB standings by division, wildcard, conference, and overall league.

    Returns:
        dict: Dict containing all standings by each category.
    """

    # Call the MLB standings API and store the JSON results.
    # TODO: Implement MLB API call for standings.
    standings_json = {}

    standings = {
        'division': {
            'divisions': {},
            'playoff_cutoff_soft': None
        },
        'wildcard': {
            'conferences': {},
            'playoff_cutoff_hard': None,
            'playoff_cutoff_soft': None
        },
        'conference': {
            'conferences': {}
        },
        'league': {
            'leagues': {
                'MLB': {
                    'abrv': 'MLB',
                    'teams': []
                }
            }
        }
    }

    # TODO: Parse standings_json and populate standings dict structure

    return standings


def determine_team_abbreviation(team_abrv):
    """ Gets team ID (int) based on team abbreviation.

    Args:
        team_abrv (str): Abbreviation of the MLB team.

    Returns:
        int: Team ID.
    """

    # Mapping of MLB teams abbreviations to IDs. Needed since schedule API only accepts ID as input.
    team_abbreviations_to_ids = {
        'ATH': 133,
        'PIT': 134,
        'SD':  135,
        'SEA': 136,
        'SF':  137,
        'STL': 138,
        'TB':  139,
        'TEX': 140,
        'TOR': 141,
        'MIN': 142,
        'PHI': 143,
        'ATL': 144,
        'CWS': 145,
        'MIA': 146,
        'NYY': 147,
        'MIL': 158,
        'LAA': 108,
        'AZ':  109,
        'BAL': 110,
        'BOS': 111,
        'CHC': 112,
        'CIN': 113,
        'CLE': 114,
        'COL': 115,
        'DET': 116,
        'HOU': 117,
        'KC':  118,
        'LAD': 119,
        'WSH': 120,
        'NYM': 121
    }

    return team_abbreviations_to_ids.get(team_abrv, None)