"""_summary_
"""
from loguru import logger
from ratelimit import limits, sleep_and_retry
from utils import data_parser
from utils.config import config
from utils.utils import build_league_key, build_player_key, build_team_key
from utils.yahoo_api import YahooAPI

logger.info("Data Parsing")

seasons = config.league_info["season"]
game_ids = config.league_info["game_id"]
league_ids = config.league_info["league_id"]
team_ids = [idx + 1 for idx, team_id in enumerate(config.league_info["teams"])]

league_info = [
    {"season": season, "game_id": game_id, "league_id": league_id, "league_key": build_league_key(game_id, league_id)}
    for season, game_id, league_id in zip(seasons, game_ids, league_ids, strict=True)
]

first_time = {"get_all_game_keys": YahooAPI.get_all_game_keys}

preseason = {
    "get_games_preseason": YahooAPI.get_games_preseason,
    "get_leagues_preseason": YahooAPI.get_leagues_preseason,
    "get_players_preseason": YahooAPI.get_players_preseason,
}

postdraft = {
    "get_leagues_postdraft": YahooAPI.get_leagues_postdraft,
    "get_players_postdraft": YahooAPI.get_players_postdraft,
}

weekly = {
    "get_leagues_weekly": YahooAPI.get_leagues_weekly,
    "get_players_weekly": YahooAPI.get_players_weekly,
}

daily = {
    "get_teams_daily": YahooAPI.get_teams_daily,
}

live = {
    "get_teams_live": YahooAPI.get_teams_live,
}

# @sleep_and_retry
# @limits(calls=15, period=900)
# def callrest(method, url, data):
#     print(method, url, data)

# game_code = "nfl"
# season = 2022
# game_id = 414
# league_id = 77446
# league_player_limit = 1_000
# league_player_limit = 25
# team_id = 1
# player_id = 27624
# week = 12

# retries = 5
# backoff = 60

# season_param = {"season": season}
# game_id_param = {"game_id": game_id}
# game_key_param = {"game_key": game_key}
# player_count_limit_param = {"player_count_limit": league_player_limit}
# player_count_start_param = {"player_count_start": 0}
# chosen_week_param = {"chosen_week": chosen_week}
# team_id_param = {"team_id": team_id}
# player_key_param = {"player_key": player_key}
