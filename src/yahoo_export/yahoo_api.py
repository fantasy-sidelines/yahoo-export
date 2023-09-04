import logging
import time
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path

import pytz
import requests
import yaml
from authlib.integrations.requests_client import OAuth2Auth, OAuth2Session
from ratelimit import limits, sleep_and_retry
from requests import Response
from requests.exceptions import HTTPError

from yahoo_export.utils.config import config
from yahoo_export.utils.utils import YahooEndpoints, mkdir_not_exists

mkdir_not_exists("secrets")


class YahooAPI:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._client = OAuth2Session(
            config.yahoo_consumer_key.get_secret_value(),
            config.yahoo_consumer_secret.get_secret_value(),
            authorize_endpoint=YahooEndpoints.AUTHORIZE_ENDPOINT.value,
            token_endpoint=YahooEndpoints.ACCESS_TOKEN_ENDPOINT.value,
        )
        self.requests = 0

    def __get_token(self) -> None:
        if Path(config.token_file_path).is_file():
            with open(config.token_file_path) as file:
                self._token = yaml.load(file, Loader=yaml.SafeLoader)
            self.__ensure_active_token()

        else:
            authorization_response, self._state = self._client.create_authorization_url(
                YahooEndpoints.AUTHORIZE_ENDPOINT.value,
                redirect_uri=YahooEndpoints.REDIRECT_ENDPOINT.value,
            )

            code_verifier = input(f"AUTH URL:\n\t{authorization_response} \nCode verifier from url: ")
            self._token["token_time"] = round(time.time())
            self._token["state"] = self._state
            self._token["client_id"] = config.yahoo_consumer_key.get_secret_value()
            self._token["client_secret"] = config.yahoo_consumer_secret.get_secret_value()

            self._token.update(
                self._client.fetch_token(
                    YahooEndpoints.ACCESS_TOKEN_ENDPOINT.value,
                    authorization_response=authorization_response,
                    grant_type="authorization_code",
                    headers=config.headers.model_dump(),
                    redirect_uri=YahooEndpoints.REDIRECT_ENDPOINT.value,
                    code=code_verifier,
                )
            )

            with open(config.token_file_path, "w") as file:
                yaml.dump(self._token, file)

    def __ensure_active_token(self) -> None:
        if self._token["expires_at"] <= round(time.time() + (60 * 5)):
            logging.warning("Token being refreshed, requests performed = %s", self.requests)
            auth_creds = {
                "client_id": self._token["client_id"],
                "client_secret": self._token["client_secret"],
                "token_time": round(time.time()),
                "state": self._token["state"],
            }
            self._token.update(
                self._client.refresh_token(
                    YahooEndpoints.ACCESS_TOKEN_ENDPOINT.value,
                    refresh_token=self._token["refresh_token"],
                    headers=config.headers.model_dump(),
                )
            )
            self._token.update(auth_creds)

            with open(config.token_file_path, "w") as file:
                yaml.dump(self._token, file)

    def get_oauth_token(self) -> dict[str, str]:
        self.__get_token()
        return OAuth2Auth(self._token)

    @sleep_and_retry
    @limits(calls=3, period=4)
    def _query(self, endpoint_url: str, params: dict[str, str] | None = None) -> Response:
        if not params:
            params = {"format": config.output_format}
        try:
            auth_token = self.get_oauth_token()
            response = self._session.get(url=endpoint_url, auth=auth_token, params=params)
            self.requests += 1
            # check status code first or raise for status?
            response.raise_for_status()
            try:
                json_data = response.json()
            except JSONDecodeError as json_err:
                json_err_msg = (
                    f"JSONDecodeError while attempting to decode response from Yahoo API endopoint: {endpoint_url}."
                )
                raise HTTPError(json_err_msg) from json_err

            return json_data

        except requests.exceptions.HTTPError as http_err:
            if (
                response.status_code == 400  # noqa: PLR2004
                and "Player key 348.p.28980 does not exist." in response.text
            ):
                logging.error(
                    "400 Error: %s\n%s\n%s",
                    endpoint_url,
                    response.headers,
                    response.text,
                    exc_info=True,
                )
                return {"2015 Error": "Player key 348.p.28980 does not exist."}
            else:
                http_err_msg = f"HTTP Error while attempting to query Yahoo API endopoint: {endpoint_url}."
                logging.info(
                    f"Total Requests = {self.requests}, Time to complete = {(time.time()-self.start_time):0.2f}"
                )
                logging.error(
                    "HTTP Error while attempting to query Yahoo API endopoint: %s\n%s\n%s",
                    endpoint_url,
                    response.headers,
                    response.text,
                    exc_info=True,
                )
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

    def get_all_game_keys(self) -> tuple[Response, str | datetime]:
        query_url = YahooEndpoints.BASE_ENDPOINT.value + YahooEndpoints.ALL_GAME_KEYS.value
        query_url = query_url.format(game_code=config.game_code)
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp

    def get_game(self, game_key: int | str) -> tuple[Response, str | datetime]:
        query_url = (
            YahooEndpoints.BASE_ENDPOINT.value + YahooEndpoints.GAMES.value + YahooEndpoints.GAMES_PRESEASON.value
        )
        query_url = query_url.format(game_key=str(game_key))
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp

    def get_league_preseason(self, league_key: str) -> tuple[Response, str | datetime]:
        query_url = (
            YahooEndpoints.BASE_ENDPOINT.value + YahooEndpoints.LEAGUES.value + YahooEndpoints.LEAGUES_PRESEASON.value
        )
        query_url = query_url.format(league_key=league_key)
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp

    def get_league_draft_result(self, league_key: str) -> tuple[Response, str | datetime]:
        query_url = (
            YahooEndpoints.BASE_ENDPOINT.value
            + YahooEndpoints.LEAGUES.value
            + YahooEndpoints.LEAGUES_DRAFT_RESULTS.value
        )
        query_url = query_url.format(league_key=league_key)
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp

    def get_league_matchup(self, league_key: str, week: int | None = None) -> tuple[Response, str | datetime]:
        chosen_week = str(week) if week else str(config.current_nfl_week)
        query_url = (
            YahooEndpoints.BASE_ENDPOINT.value + YahooEndpoints.LEAGUES.value + YahooEndpoints.LEAGUES_MATCHUPS.value
        )
        query_url = query_url.format(league_key=league_key, week=chosen_week)
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d_%H-%M-%ST%z")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp

    def get_league_transaction(self, league_key: str) -> tuple[Response, str | datetime]:
        query_url = (
            YahooEndpoints.BASE_ENDPOINT.value
            + YahooEndpoints.LEAGUES.value
            + YahooEndpoints.LEAGUES_TRANSACTIONS.value
        )
        query_url = query_url.format(league_key=league_key)
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp

    def get_league_offseason(self, league_key: str) -> tuple[Response, str | datetime]:
        query_url = (
            YahooEndpoints.BASE_ENDPOINT.value + YahooEndpoints.LEAGUES.value + YahooEndpoints.LEAGUES_OFFSEASON.value
        )
        query_url = query_url.format(league_key=league_key)
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp

    def get_roster(self, team_key_list: list[str], week: int | None = None) -> tuple[Response, str | datetime]:
        chosen_week = str(week) if week else str(config.current_nfl_week)
        query_url = YahooEndpoints.BASE_ENDPOINT.value + YahooEndpoints.TEAMS.value + YahooEndpoints.TEAMS_ROSTER.value
        query_url = query_url.format(team_key_list=",".join(team_key_list), week=chosen_week)
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d_%H-%M-%ST%z")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp

    def get_player(
        self, league_key: str, start_count: int = 0, retrieval_limit: int = 25
    ) -> tuple[Response, str | datetime]:
        query_url = YahooEndpoints.BASE_ENDPOINT.value + YahooEndpoints.PLAYERS.value + YahooEndpoints.PLAYERS_ALL.value
        query_url = query_url.format(
            league_key=league_key,
            start_count=str(start_count),
            retrieval_limit=str(retrieval_limit),
        )
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp

    def get_player_draft_analysis(self, league_key: str, player_key_list: list[str]) -> tuple[Response, str | datetime]:
        query_url = (
            YahooEndpoints.BASE_ENDPOINT.value
            + YahooEndpoints.PLAYERS.value
            + YahooEndpoints.PLAYERS_DRAFT_ANALYSIS.value
        )
        query_url = query_url.format(league_key=league_key, player_key_list=",".join(player_key_list))
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp

    def get_player_stat(
        self, league_key: str, player_key_list: list[str], week: int | None = None
    ) -> tuple[Response, str | datetime]:
        chosen_week = str(week) if week else str(config.current_nfl_week)
        query_url = (
            YahooEndpoints.BASE_ENDPOINT.value + YahooEndpoints.PLAYERS.value + YahooEndpoints.PLAYERS_STATS.value
        )
        query_url = query_url.format(league_key=league_key, player_key_list=",".join(player_key_list), week=chosen_week)
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d_%H-%M-%ST%z")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp

    def get_player_pct_owned(
        self, league_key: str, player_key_list: list[str], week: int | None = None
    ) -> tuple[Response, str | datetime]:
        chosen_week = str(week) if week else str(config.current_nfl_week)
        query_url = (
            YahooEndpoints.BASE_ENDPOINT.value
            + YahooEndpoints.PLAYERS.value
            + YahooEndpoints.PLAYERS_PERCENT_OWNED.value
        )
        query_url = query_url.format(league_key=league_key, player_key_list=",".join(player_key_list), week=chosen_week)
        query_timestamp = datetime.now(pytz.utc).strftime("%Y-%m-%d_%H-%M-%ST%z")
        response = self._query(endpoint_url=query_url)
        return response, query_timestamp
