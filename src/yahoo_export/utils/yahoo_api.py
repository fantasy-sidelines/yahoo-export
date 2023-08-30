"""_summary_

Raises:
    HTTPError: _description_
    HTTPError: _description_
    HTTPError: _description_
    HTTPError: _description_

Returns:
    _type_: _description_
"""
import json
import logging
import sys
import time
from json import JSONDecodeError
from pathlib import Path

import requests
import yaml
from authlib.integrations.requests_client import OAuth2Auth, OAuth2Session
from loguru import logger
from requests import Response
from requests.exceptions import HTTPError
from utils.config import config, secrets_config
from utils.utils import (
    HTTPStatusCodes,
    YahooEndpoints,
    mkdir_not_exists,
    write_json_file,
)

logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")

logger.info("Yahoo API")

logging.getLogger("yahoo_oauth").setLevel(level=logging.INFO)

mkdir_not_exists("secrets")


# token = {'token_type': 'bearer', 'access_token': '....', ...}
# auth = OAuth2Auth(token)
# requests.get(url, auth=auth)


class YahooAPI:
    """_summary_"""

    def __init__(self) -> None:
        """_summary_"""
        self.executed_queries = []
        self.pulled_from_saved = []
        self._session = requests.Session()
        self._auth_token = self.get_oauth_token()

    def _get_token(self) -> None:
        """_summary_"""
        self._client = OAuth2Session(
            secrets_config.yahoo_consumer_key.get_secret_value(),
            secrets_config.yahoo_consumer_secret.get_secret_value(),
            authorize_endpoint=str(config.authorize_endpoint),
            token_endpoint=str(config.access_token_endpoint),
        )
        if Path(config.token_file_path).is_file():
            with open(config.token_file_path) as file:
                self._token = yaml.load(file, Loader=yaml.SafeLoader)
            self._ensure_active_token()

        else:
            authorization_response, self._state = self._client.create_authorization_url(
                str(config.authorize_endpoint),
                redirect_uri=str(config.redirect_endpoint),
            )

            code_verifier = input(f"AUTH URL:\n\t{authorization_response} \nCode verifier from url: ")
            self._token["token_time"] = round(time.time())
            self._token["state"] = self._state
            self._token["client_id"] = secrets_config.yahoo_consumer_key.get_secret_value()
            self._token["client_secret"] = secrets_config.yahoo_consumer_secret.get_secret_value()

            self._token.update(
                self._client.fetch_token(
                    str(config.access_token_endpoint),
                    authorization_response=authorization_response,
                    grant_type="authorization_code",
                    headers=config.headers.model_dump(),
                    redirect_uri=str(config.redirect_endpoint),
                    code=code_verifier,
                )
            )

            with open(config.token_file_path, "w") as file:
                yaml.dump(self._token, file)

    def _ensure_active_token(self) -> None:
        """_summary_"""
        if self._token["expires_at"] <= round(time.time() + (60 * 5)):
            auth_creds = {
                "client_id": self._token["client_id"],
                "client_secret": self._token["client_secret"],
                "token_time": round(time.time()),
                "state": self._token["state"],
            }
            self._token.update(
                self._client.refresh_token(
                    str(config.access_token_endpoint),
                    refresh_token=self._token["refresh_token"],
                    headers=config.headers.model_dump(),
                )
            )
            self._token.update(auth_creds)

            with open(config.token_file_path, "w") as file:
                yaml.dump(self._token, file)

    def get_oauth_token(self) -> dict[str, str]:
        """_summary_

        Returns:
            dict[str, str]: _description_
        """
        self._get_token()
        return OAuth2Auth(self._token)

    def handle_status_code(self, status_code: int) -> None:
        """Handle status codes from Yahoo API.

        Args:
            status_code (int): Status code retured from Yahoo API.
        """

        if status_code == HTTPStatusCodes.OK:
            # loguru.logger.info(f"Status code: {status_code}")
            pass
        elif status_code == HTTPStatusCodes.NO_CONTENT:
            pass
        elif status_code == HTTPStatusCodes.PARTIAL_CONTENT:
            pass
        elif status_code == HTTPStatusCodes.BAD_REQUEST:
            pass
        elif status_code == HTTPStatusCodes.UNAUTHORIZED:
            pass
        elif status_code == HTTPStatusCodes.FORBIDDEN:
            pass
        elif status_code == HTTPStatusCodes.NOT_FOUND:
            pass
        elif status_code == HTTPStatusCodes.INTERNAL_SERVER_ERROR:
            pass
        elif status_code == HTTPStatusCodes.NOT_IMPLEMENTED:
            pass
        elif status_code == HTTPStatusCodes.SERVICE_UNAVAILABLE:
            pass
        elif status_code == HTTPStatusCodes.RATE_LIMIT:
            pass
        else:
            status_code_err = f"Status code: {status_code} not handled."
            raise HTTPError(status_code_err)

    def _query(self, endpoint_url: str, params: dict[str, str] | None = None, **kwargs) -> Response:
        if not params:
            params = {"format": "json"}
        file_name = Path(config.data_cache_path) / str(config.current_nfl_season) / kwargs["path"]
        try:
            if file_name.is_file() and config.use_saved_data:
                with open(file_name) as file:
                    return json.load(file)
            else:
                response = self._session.get(url=endpoint_url, auth=self._auth_token, params=params)
                status_code = response.status_code
                self.handle_status_code(status_code)
                # check status code first or raise for status?
                response.raise_for_status()
                try:
                    json_data = response.json()
                except JSONDecodeError as json_err:
                    json_err_msg = (
                        f"JSONDecodeError while attempting to decode response from Yahoo API endopoint: {endpoint_url}."
                    )
                    raise HTTPError(json_err_msg) from json_err
                if config.save_to_json:
                    write_json_file(
                        json_data=json_data,
                        file_name=file_name,
                    )
                return json_data

        except requests.exceptions.HTTPError as http_err:
            http_err_msg = f"HTTP Error while attempting to query Yahoo API endopoint: {endpoint_url}."
            raise HTTPError(http_err_msg) from http_err

        except requests.exceptions.ConnectionError as con_err:
            con_err_msg = f"Connection error while attempting to query Yahoo API endopoint: {endpoint_url}."
            raise HTTPError(con_err_msg) from con_err

        except requests.exceptions.Timeout as to_err:
            timeout_err_msg = f"Timeout error while attempting to query Yahoo API endopoint: {endpoint_url}."
            raise HTTPError(timeout_err_msg) from to_err

        except requests.exceptions.RequestException as err:
            err_msg = f"Error while attempting to query Yahoo API endopoint: {endpoint_url}."
            raise HTTPError(err_msg) from err

    def get_all_game_keys(self) -> Response:
        """_summary_

        Returns:
            Response: _description_
        """
        query_url = str(str(config.yahoo_base_url)) + YahooEndpoints.ALL_GAME_KEYS.value
        query_url = query_url.format(
            game_code=config.game_code,
        )
        return self._query(endpoint_url=query_url, path="games/all_keys.json")

    def get_games_preseason(self, game_key_list: list[int | str]) -> Response:
        """_summary_

        Args:
            game_key_list (list[int  |  str]): _description_

        Returns:
            Response: _description_
        """
        query_url = str(config.yahoo_base_url) + YahooEndpoints.GAMES.value + YahooEndpoints.GAMES_PRESEASON.value
        query_url = query_url.format(
            game_key_list=",".join(game_key_list),
        )
        return self._query(endpoint_url=query_url, path="games/preseason.json")

    def get_leagues_preseason(self, league_key_list: list[str]) -> Response:
        """_summary_

        Args:
            league_key_list (list[str]): _description_

        Returns:
            Response: _description_
        """
        query_url = str(config.yahoo_base_url) + YahooEndpoints.LEAGUES.value + YahooEndpoints.LEAGUES_PRESEASON.value
        query_url = query_url.format(
            game_key_list=",".join(league_key_list),
        )
        return self._query(endpoint_url=query_url, path="leagues/preason.json")

    def get_leagues_postdraft(self, league_key_list: list[str]) -> Response:
        """_summary_

        Args:
            league_key_list (list[str]): _description_

        Returns:
            Response: _description_
        """
        query_url = str(config.yahoo_base_url) + YahooEndpoints.LEAGUES.value + YahooEndpoints.LEAGUES_POSTDRAFT.value
        query_url = query_url.format(
            game_key_list=",".join(league_key_list),
        )
        return self._query(endpoint_url=query_url, path="leagues/postdraft.json")

    def get_leagues_weekly(self, league_key_list: list[str]) -> Response:
        """_summary_

        Args:
            league_key_list (list[str]): _description_

        Returns:
            Response: _description_
        """
        query_url = str(config.yahoo_base_url) + YahooEndpoints.LEAGUES.value + YahooEndpoints.LEAGUES_WEEKLY.value
        query_url = query_url.format(
            game_key_list=",".join(league_key_list),
        )
        return self._query(endpoint_url=query_url, path=f"leagues/weekly/week_{config.current_nfl_week}.json")

    def get_leagues_offseason(self, league_key_list: list[str]) -> Response:
        """_summary_

        Args:
            league_key_list (list[str]): _description_

        Returns:
            Response: _description_
        """
        query_url = str(config.yahoo_base_url) + YahooEndpoints.LEAGUES.value + YahooEndpoints.LEAGUES_OFFSEASON.value
        query_url = query_url.format(
            game_key_list=",".join(league_key_list),
        )
        return self._query(endpoint_url=query_url, file_path="leagues/offseason.json")

    def get_teams_daily(self, team_key_list: list[str], week: int) -> Response:
        """_summary_

        Args:
            team_key_list (list[str]): _description_
            week (int): _description_

        Returns:
            Response: _description_
        """
        query_url = str(config.yahoo_base_url) + YahooEndpoints.TEAMS.value + YahooEndpoints.TEAMS_DAILY.value
        query_url = query_url.format(
            team_key_list=",".join(team_key_list),
            week=str(week),
        )
        return self._query(endpoint_url=query_url, path=f"teams/daily/{config.current_date}.json")

    def get_teams_live(self, team_key_list: list[str], week: int) -> Response:
        """_summary_

        Args:
            team_key_list (list[str]): _description_
            week (int): _description_

        Returns:
            Response: _description_
        """
        query_url = str(config.yahoo_base_url) + YahooEndpoints.TEAMS.value + YahooEndpoints.TEAMS_LIVE.value
        query_url = query_url.format(
            team_key_list=",".join(team_key_list),
            week=str(week),
        )
        return self._query(endpoint_url=query_url, path=f"teams/daily/{config.current_timestamp}.json")

    def get_players_preseason(self, league_key: str, start_count: int = 0, retrieval_limit: int = 25) -> Response:
        """Once reaching the end of the players, the `players` list will be less than retrieval limit.
        1,163 total in 2023

        Args:
            league_key (str): _description_
            start_count (int, optional): _description_. Defaults to 0.
            retrieval_limit (int, optional): _description_. Defaults to 25.

        Returns:
            Response: _description_
        """
        query_url = str(config.yahoo_base_url) + YahooEndpoints.PLAYERS.value + YahooEndpoints.PLAYERS_PRESEASON.value
        query_url = query_url.format(
            league_key=league_key,
            start_count=str(start_count),
            retrieval_limit=str(retrieval_limit),
        )
        return self._query(endpoint_url=query_url, path="teams/preasons.json")

    def get_players_postdraft(self, league_key: str, player_key_list: list[str]) -> Response:
        """_summary_

        Args:
            league_key (str): _description_
            player_key_list (list[str]): _description_

        Returns:
            Response: _description_
        """
        query_url = str(config.yahoo_base_url) + YahooEndpoints.PLAYERS.value + YahooEndpoints.PLAYERS_DRAFT.value
        query_url = query_url.format(
            league_key=league_key,
            player_key_list=",".join(player_key_list),
        )
        return self._query(endpoint_url=query_url, path="players/postdraft.json")

    def get_players_weekly(self, league_key: str, player_key_list: list[str]) -> Response:
        """_summary_

        Args:
            league_key (str): _description_
            player_key_list (list[str]): _description_

        Returns:
            Response: _description_
        """
        query_url = str(config.yahoo_base_url) + YahooEndpoints.PLAYERS.value + YahooEndpoints.PLAYERS_WEEKLY.value
        query_url = query_url.format(
            league_key=league_key,
            player_key_list=",".join(player_key_list),
        )
        return self._query(endpoint_url=query_url, path=f"players/week_{config.current_nfl_week}.json")
