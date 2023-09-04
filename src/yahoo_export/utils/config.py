import base64
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, HttpUrl, SecretStr, computed_field
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from yahoo_export.utils.utils import mkdir_not_exists


class YAMLConfigSettingsSource(PydanticBaseSettingsSource):
    def get_field_value(
        self,
        field: FieldInfo,  # noqa: ARG002
        field_name: str,
    ) -> tuple[Any, str, bool]:
        encoding = self.config.get("env_file_encoding")  # noqa: F841
        with open(Path("yahoo_export_config.yaml")) as yaml_file:
            file_content_yaml = yaml.load(yaml_file, Loader=yaml.SafeLoader)
        field_value = file_content_yaml.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(
        self,
        field_name: str,  # noqa: ARG002
        field: FieldInfo,  # noqa: ARG002
        value: Any,
        value_is_complex: bool,  # noqa: ARG002, FBT001
    ) -> Any:
        return value

    def __call__(self) -> dict[str, Any]:
        d: dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(field, field_name)
            field_value = self.prepare_field_value(field_name, field, field_value, value_is_complex)
            if field_value is not None:
                d[field_key] = field_value

        return d


# @dataclass
class OAuthHeaders(BaseModel):
    accept: str
    authorization: str
    content_type: str


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file_encoding="utf-8", secrets_dir="secrets")
    yahoo_consumer_key: SecretStr = SecretStr("")
    yahoo_consumer_secret: SecretStr = SecretStr("")
    token_file_path: str | None = None
    yahoo_base_url: HttpUrl = HttpUrl("https://fantasysports.yahooapis.com/fantasy/v2/")
    authorize_endpoint: HttpUrl = HttpUrl("https://api.login.yahoo.com/oauth2/request_auth")
    access_token_endpoint: HttpUrl = HttpUrl("https://api.login.yahoo.com/oauth2/get_token")
    redirect_endpoint: HttpUrl | str = "oob"
    game_code: str = "nfl"
    output_format: str = "json"
    current_nfl_season: int | None = 2023
    current_nfl_week: int | None = 0
    league_info: dict[str, Any]

    @computed_field
    @property
    def encoded_credentials(self) -> Any:
        return base64.b64encode(
            f"{self.yahoo_consumer_key.get_secret_value()}:{self.yahoo_consumer_secret.get_secret_value()}".encode()
        )

    @computed_field
    @property
    def token_file_path(self) -> Any:
        if self.token_file_path is None:
            return str(Path("secrets/oauth_token.yaml").as_posix())
        return self.token_file_path

    @computed_field
    @property
    def data_cache_path(self) -> Any:
        if self.data_cache_path is None:
            data_cache_path = str((Path.cwd() / "data_cache").as_posix())
        else:
            data_cache_path = str((Path.cwd() / self.data_cache_path).as_posix())
        mkdir_not_exists(data_cache_path)
        return data_cache_path

    @computed_field
    @property
    def headers(self) -> Any:
        headers = OAuthHeaders(
            **{
                "accept": f"application/{self.output_format}",
                "authorization": f"Basic {self.encoded_credentials.decode()}",
                "content_type": "application/x-www-form-urlencoded",
            }
        )
        return headers

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            YAMLConfigSettingsSource(settings_cls),
            env_settings,
            file_secret_settings,
            dotenv_settings,
        )


config = Config()  # type: ignore
