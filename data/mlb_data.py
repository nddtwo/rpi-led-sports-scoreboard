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
            
    return games


def get_next_game(team):
    """ Loads next game details for the supplied MLB team.
    If the team is currently playing, will return details of the current game.

    Args:
        team (str): Team abbreviation to pull next game details for.

    Returns:
            dict: Dict of next game details.
    """
    
    # Note the current datetime.
    cur_datetime = dt.today().astimezone()
    cur_date = dt.today().astimezone().date()

    # Call the MLB schedule API for the team specified and store the JSON results.
    # TODO: Implement MLB API call for team schedule.
    schedule_json = []

    # Filter results to games that have not already concluded. Get the 0th element, the next game.
    upcoming_games = []  # TODO: Filter schedule_json for upcoming games
    next_game_details = upcoming_games[0] if len(upcoming_games) > 0 else None

    if next_game_details:
        # Put together a dictionary with needed details.
        next_game = {
            'home_or_away': None,  # TODO: Extract from API
            'opponent_abrv': None,  # TODO: Extract from API
            'start_datetime_utc': None,  # TODO: Extract from API
            'start_datetime_local': None,  # TODO: Extract from API
            'is_today': False,  # TODO: Determine from API
            'has_started': False  # TODO: Determine from API
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
