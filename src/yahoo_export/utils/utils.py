from collections import deque
from enum import Enum
from pathlib import Path


def mkdir_not_exists(dir_name: str) -> None:
    cwd_path = Path.cwd()
    check_dir = cwd_path / dir_name
    check_dir.mkdir(parents=True, exist_ok=True)


def chunk_list(input_list: list, chunk_size: int):
    deque_obj = deque(input_list)

    while deque_obj:
        chunk = []
        for _ in range(chunk_size):
            if deque_obj:
                chunk.append(deque_obj.popleft())

        yield chunk


class YahooEndpoints(Enum):
    BASE_ENDPOINT = "https://fantasysports.yahooapis.com/fantasy/v2"
    AUTHORIZE_ENDPOINT = "https://api.login.yahoo.com/oauth2/request_auth"
    ACCESS_TOKEN_ENDPOINT = "https://api.login.yahoo.com/oauth2/get_token"
    REDIRECT_ENDPOINT = "oob"

    ALL_GAME_KEYS = "/games;game_codes={game_code}"

    GAMES = "/game/{game_key};"
    GAMES_PRESEASON = "out=metadata,game_weeks,stat_categories,position_types,roster_positions"

    LEAGUES = "/league/{league_key}"
    LEAGUES_PRESEASON = ";out=metadata,settings,teams"
    LEAGUES_DRAFT_RESULTS = ";out=draftresults,teams"
    LEAGUES_MATCHUPS = "/scoreboard;type=week;week={week}"
    LEAGUES_TRANSACTIONS = "/transactions"
    LEAGUES_OFFSEASON = ";out=metadata,settings,draftresults,teams,transactions"

    TEAMS = "/teams;team_keys={team_key_list}"
    TEAMS_ROSTER = "/roster;type=week;week={week}"

    PLAYERS = "/league/{league_key}/players;"
    PLAYERS_ALL = "start={start_count};count={retrieval_limit}"
    PLAYERS_DRAFT_ANALYSIS = "player_keys={player_key_list}/draft_analysis"
    PLAYERS_STATS = "player_keys={player_key_list}/stats;type=week;week={week}"
    PLAYERS_PERCENT_OWNED = "player_keys={player_key_list}/percent_owned;type=week;week={week}"
