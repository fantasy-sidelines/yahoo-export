"""_summary_

Returns:
    _type_: _description_
"""
import json

import polars as pl
from loguru import logger

logger.info("Data Parsing")

data_type = str | dict | list


class YFPYParseBase:
    """_summary_"""

    def __init__(self, response: str) -> None:
        """_summary_

        Args:
            response (str): _description_
        """
        self.nested_keys = set()
        self.list_of_dicts = []

        if isinstance(response, str):
            data = json.loads(response)
            self.data = self._unnest(data)

        elif isinstance(response, dict):
            self.data = self._unnest(response)

        elif isinstance(response, list):
            self.data = response

    def _list_parse(self, parse_key: str, parse_list: list) -> pl.DataFrame:
        """_summary_

        Args:
            parse_key (str): _description_
            parse_list (list): _description_

        Returns:
            pl.DataFrame: _description_
        """
        df = pl.from_dicts([row[parse_key] for row in parse_list])
        return df

    def _unnest(
        self, parse_dict: dict[str, data_type] | list[dict[str, data_type]]
    ) -> list[dict[str, str]] | dict[str, str]:
        """_summary_

        Args:
            parse_dict (dict[str, data_type] | list[dict[str, data_type]]): _description_

        Returns:
            list[dict[str, str]] | dict[str, str]: _description_
        """
        new_dict = {}
        list_dicts = []

        for key, val in parse_dict.items():
            if isinstance(val, dict) and len(val.keys()) == 1:
                new_key = list(val.keys())[0]

                if isinstance(val.get(new_key), list):
                    list_dicts.append(self._unnest(val))

                elif isinstance(val.get(new_key), dict):
                    new_val = {f"{new_key}_{k}": v for k, v in val.get(new_key).items()}
                    new_dict[new_key] = new_val
                    self.nested_keys.add(new_key)

                else:
                    new_dict[new_key] = val.get(new_key)

            elif isinstance(val, dict) and len(val.keys()) != 1:
                new_val = {f"{key}_{k}": v for k, v in val.items()}
                new_dict[key] = new_val
                self.nested_keys.add(key)

            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        sub_dict = self._unnest(item)
                        list_dicts.append(sub_dict)

            else:
                new_dict[key] = val

        if new_dict != {}:
            self.list_of_dicts.append(new_dict)

        res = list_dicts or new_dict

        return res

    def parse_data(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        norm_dict = {key: val for key, val in self.data.items() if key not in self.nested_keys}
        df = pl.DataFrame(norm_dict)

        return df


class GameKeyParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_game_keys(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self._list_parse("game", self.data)

        return df


class LeagueMetadataParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_league_metadata(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self.parse_data()

        return df


class TeamMetadataParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_team_metadata(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self.parse_data()

        df = pl.concat(
            [
                df,
                *[pl.from_dict(self.data.get(nested)) for nested in self.nested_keys],
            ],
            how="horizontal",
        )

        return df


class PositionTypeParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_position_types(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self._list_parse("position_type", self.data)

        return df


class RosterPositionParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_roster_positions(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self._list_parse("roster_position", self.data)

        return df


class StatCategoryParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_stat_categories(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self._list_parse("stat", self.data)

        return df


class WeekParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_weeks(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self._list_parse("game_week", self.data)

        return df


class DraftResultParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_draft_results(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self._list_parse("draft_result", self.data)

        return df


class MatchupParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_matchups(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self._list_parse("matchup", self.data)

        if all("matchup_" in col for col in df.columns):
            df = df.rename({col: col[len("matchup_") :] for col in df.columns})

        team_1_df = (
            df.select(pl.col("teams").list.get(0).alias("teams_1"))
            .unnest("teams_1")
            .select(pl.col("team"))
            .unnest(["team"])
            .unnest(["team_points"])
            .select(
                pl.col("team_key").alias("team_1_key"),
                pl.col("win_probability").alias("team_1_win_probability"),
                pl.col("team_projected_points"),
                pl.col("name").alias("team_1_name"),
                pl.col("total").alias("team_1_points"),
            )
            .unnest(["team_projected_points"])
            .select(
                pl.col("team_1_key", "team_1_win_probability", "team_1_name", "team_1_points"),
                pl.col("total").alias("team_1_projected_points"),
            )
        )

        team_2_df = (
            df.select(pl.col("teams").list.get(1).alias("teams_2"))
            .unnest("teams_2")
            .select(pl.col("team"))
            .unnest(["team"])
            .unnest(["team_points"])
            .select(
                pl.col("team_key").alias("team_2_key"),
                pl.col("win_probability").alias("team_2_win_probability"),
                pl.col("team_projected_points"),
                pl.col("name").alias("team_2_name"),
                pl.col("total").alias("team_2_points"),
            )
            .unnest(["team_projected_points"])
            .select(
                pl.col("team_2_key", "team_2_win_probability", "team_2_name", "team_2_points"),
                pl.col("total").alias("team_2_projected_points"),
            )
        )

        teams_df = pl.concat([team_1_df, team_2_df], how="horizontal")

        grade_1_df = (
            df.select(pl.col("matchup_grades").list.get(0).alias("matchup_grades_1"))
            .unnest("matchup_grades_1")
            .select(pl.col("matchup_grade"))
            .unnest(["matchup_grade"])
            .select(pl.col("grade").alias("matchup_grade_1"))
        )

        grade_2_df = (
            df.select(pl.col("matchup_grades").list.get(1).alias("matchup_grades_2"))
            .unnest("matchup_grades_2")
            .select(pl.col("matchup_grade"))
            .unnest(["matchup_grade"])
            .select(pl.col("grade").alias("matchup_grade_2"))
        )

        grades_df = pl.concat([grade_1_df, grade_2_df], how="horizontal")
        df = pl.concat([df, teams_df, grades_df], how="horizontal")

        return df


class PlayerParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_player(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self._list_parse("player", self.data)
        df = (
            df.unnest("headshot")
            .select(pl.all().exclude("url", "size"), pl.col("url").alias("headshot_url"))
            .unnest("name")
        )

        return df


class SettingParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_settings(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = pl.from_dict(self.list_of_dicts[-1])

        return df

    def parse_stat_settings(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = pl.from_dicts(stat for stat in self.list_of_dicts if list(stat.keys())[0] == "stat").unnest("stat")

        df = df.select(
            pl.all().exclude("stat_stat_position_types"),
            pl.col("stat_stat_position_types").struct.field("stat_position_type").struct.field("is_only_display_stat"),
        )

        stat_cat = df.filter(pl.col("stat_name") != None).select(pl.all().exclude("stat_value"))  # noqa: E711
        stat_mod = df.filter(pl.col("stat_name") == None).select(  # noqa: E711
            pl.col("stat_stat_id"), pl.col("stat_value").alias("stat_stat_modifier")
        )

        df = stat_cat.join(stat_mod, how="outer", on="stat_stat_id")
        df = df.rename({col: col[len("stat_") :] for col in df.columns if col[: len("stat_")] == "stat_"})

        return df

    def parse_roster_settings(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = pl.from_dicts(
            roster_pos for roster_pos in self.list_of_dicts if list(roster_pos.keys())[0] == "roster_position"
        ).unnest("roster_position")

        df = df.select(pl.all().exclude("roster_position"))

        df = df.rename(
            {
                col: col[len("roster_position_") :]
                for col in df.columns
                if col[: len("roster_position_")] == "roster_position_"
            }
        )

        return df


class StandingParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_standings(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self._list_parse("team", self.data)

        df = (
            df.select(pl.col("team_team_key").alias("team_key"), pl.col("team_team_standings").alias("team_standings"))
            .unnest("team_standings")
            .unnest("outcome_totals", "streak")
            .rename({"type": "streak_type", "value": "streak_value"})
        )

        return df


class TeamParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_teams(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self._list_parse("team", self.data).unnest("managers", "roster_adds")
        df = (
            df.rename({"url": "team_url", "coverage_value": "roster_adds_coverage_week", "value": "roster_adds_value"})
            .unnest("team_logos")
            .unnest("team_logo")
            .select(pl.all().exclude("size", "url", "coverage_type"), pl.col("url").alias("team_logo_url"))
        )

        df = df.unnest("manager").rename(
            {"image_url": "manager_image_url", "guid": "manager_guid", "name": "team_name", "nickname": "manager_name"}
        )

        return df


class TransactionParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_transactions(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = self._list_parse("transaction", self.data).rename({"type": "transaction_type"})
        max_len = df.select(pl.col("players").list.lengths().max().alias("players_len")).item()

        for i in range(max_len):
            idx = i + 1
            df = (
                df.with_columns(pl.col("players").list.get(i).alias(f"players_{idx}"))
                .unnest(f"players_{idx}")
                .unnest("player")
                .unnest("transaction_data")
                .select(
                    pl.all().exclude(
                        "display_position",
                        "editorial_team_abbr",
                        "name",
                        "player_id",
                        "player_key",
                        "position_type",
                        "destination_team_key",
                        "destination_team_name",
                        "destination_type",
                        "source_type",
                        "type",
                        "source_team_name",
                        "source_team_key",
                    ),
                    pl.col("player_key").alias(f"player_key_{idx}"),
                    pl.col("destination_team_key").alias(f"destination_team_key_{idx}"),
                    pl.col("destination_type").alias(f"destination_type_{idx}"),
                    pl.col("source_type").alias(f"source_type_{idx}"),
                    pl.col("type").alias(f"indi_trans_type_{idx}"),
                    pl.col("source_team_key").alias(f"source_team_key_{idx}"),
                )
            )

        return df


class DraftAnalysisParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_draft_analysis(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = pl.from_dict(self.data.get("draft_analysis"))
        df = df.with_columns(pl.lit(self.data.get("player_key")).alias("player_key"))

        return df


class PlayerOwnershipParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_player_ownership(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        ownership_dict = self.data.get("ownership")

        del ownership_dict["ownership_teams"]

        df = pl.from_dict(ownership_dict)

        df = df.with_columns(
            pl.lit(self.data.get("player_key")).alias("player_key"),
            pl.lit(self.data.get("week")).alias("ownership_week"),
            pl.lit(self.data.get("is_undroppable")).alias("is_undroppable"),
        )

        return df


class PlayerPercentOwnedParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_player_percent_owned(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        ownership_dict = self.data.get("percent_owned")
        df = pl.from_dict(ownership_dict)

        df = df.with_columns(
            pl.lit(self.data.get("player_key")).alias("player_key"),
            pl.lit(self.data.get("week")).alias("ownership_week"),
            pl.lit(self.data.get("is_undroppable")).alias("is_undroppable"),
        )

        return df


class PlayerStatsParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_player_stats(self) -> tuple[pl.DataFrame, pl.DataFrame]:
        """_summary_

        Returns:
            tuple[pl.DataFrame, pl.DataFrame]: _description_
        """
        player_key = self.data.get("player_key")
        player_points = self.data.get("player_points")
        player_stats = self.data.get("player_stats")
        points_df = pl.from_dict(player_points).drop("player_points_coverage_type")

        stats_df = (
            pl.from_dict(player_stats).drop("player_stats_coverage_type").unnest("player_stats_stats").unnest("stat")
        )

        points_df = points_df.with_columns(
            pl.lit(player_key).alias("player_key"),
        )

        stats_df = stats_df.with_columns(
            pl.lit(player_key).alias("player_key"),
        )

        return points_df, stats_df


class TeamRosterParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_team_roster(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = pl.from_dicts(player.get("player") for player in self.data)

        df = df.select(
            pl.col(
                "player_player_key",
                "player_eligible_positions",
                "player_primary_position",
                "player_selected_position",
                "player_status",
                "player_has_player_notes",
                "player_player_notes_last_timestamp",
            )
        ).unnest("player_selected_position")

        df = df.rename(
            {
                "player_player_key": "player_key",
                "player_eligible_positions": "eligible_positions",
                "player_primary_position": "primary_position",
                "position": "selected_position",
                "player_status": "status",
                "player_has_player_notes": "has_player_notes",
                "player_player_notes_last_timestamp": "player_notes_last_timestamp",
            }
        )

        return df


class TeamStatsParser(YFPYParseBase):
    """_summary_

    Args:
        YFPYParseBase (_type_): _description_
    """

    def parse_team_stats(self) -> pl.DataFrame:
        """_summary_

        Returns:
            pl.DataFrame: _description_
        """
        df = (
            pl.from_dict(self.data)
            .unnest("team_points", "team_projected_points")
            .drop(["team_points_coverage_type", "team_projected_points_coverage_type", "team_projected_points_week"])
        )

        return df
