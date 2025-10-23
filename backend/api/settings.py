from functools import lru_cache
import secrets

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MONGO_")

    user: str = Field(..., description="MongoDB username")
    password: str = Field(..., description="MongoDB password")
    host: str = Field("localhost", description="MongoDB host address")
    port: int = Field(27017, description="MongoDB port")
    database: str = Field("test_manager", description="MongoDB database name")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        return f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}"


class InfluxSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INFLUXDB_")

    user: str = Field(..., description="InfluxDB username")
    password: str = Field(..., description="InfluxDB password")
    host: str = Field("localhost", description="InfluxDB host address")
    port: int = Field(8086, description="InfluxDB port")
    database: str = Field("test_manager", description="InfluxDB database name")
    measurement: str = Field("logbook", description="InfluxDB measurement name")


class Settings(BaseSettings):
    # API settings
    api_host: str = Field("0.0.0.0", description="Host address")
    api_port: int = Field(8080, description="Port number")
    api_workers: int = Field(1, description="Number of workers")

    # TODO: Switch to True to test and eventually remove this to enforce authentication
    api_auth_active: bool = Field(
        False, description="Whether API authentication is active"
    )

    # Quix settings
    workspace_id: str = Field(
        alias="Quix__Workspace__Id", description="Quix workspace ID"
    )
    sdk_token: str = Field(alias="Quix__Sdk__Token", description="SDK token")

    # Blob storage settings
    secret_key: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        description="Secret key for signing URLs",
    )
    file_signature_expiration_seconds: int = Field(
        30, description="File upload signature expiration time in seconds"
    )

    # Configuration API settings
    config_api_url: str = Field(..., description="Configuration API URL")

    # Nested settings
    mongo: MongoSettings = Field(default_factory=MongoSettings)  # type: ignore[arg-type]
    influx: InfluxSettings = Field(default_factory=InfluxSettings)  # type: ignore[arg-type]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
