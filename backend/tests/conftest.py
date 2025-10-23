import subprocess
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Generator, ContextManager

import httpx
from influxdb import InfluxDBClient
import pytest
from fastapi.testclient import TestClient
from quixportal import get_filesystem
from testcontainers.mongodb import MongoDbContainer
from testcontainers.kafka import KafkaContainer
from testcontainers.influxdb import InfluxDbContainer
from testcontainers.core.generic import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.waiting_utils import wait_for_logs

from api.app import create_app
from api.settings import Settings, get_settings

from tests.utils import find_free_port

TestFactory = Callable[..., tuple[dict[str, Any], dict[str, Any]]]

PORTAL_API_PORT = find_free_port()
CONFIG_API_PORT = find_free_port()


@pytest.fixture(scope="session")
def portal_api_url() -> Generator[str, None, None]:
    """Start a mock portal API server for testing."""
    mock_server_path = Path(__file__).parent / "portal_api.py"
    process = subprocess.Popen(
        ["python", str(mock_server_path), PORTAL_API_PORT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(0.5)
    yield f"http://host.docker.internal:{PORTAL_API_PORT}"
    process.terminate()
    process.wait()


@pytest.fixture(scope="session")
def network() -> Generator[Network, None, None]:
    with Network() as network:
        yield network


@pytest.fixture(scope="session")
def mongo_container(network: Network) -> Generator[MongoDbContainer, None, None]:
    with MongoDbContainer(name="test-manager-mongo", network=network) as mongo:
        yield mongo


@pytest.fixture()
def mongo(
    monkeypatch: pytest.MonkeyPatch, mongo_container: MongoDbContainer
) -> Generator[None, None, None]:
    monkeypatch.setenv("MONGO_USER", mongo_container.username)
    monkeypatch.setenv("MONGO_PASSWORD", mongo_container.password)
    monkeypatch.setenv("MONGO_HOST", mongo_container.get_container_host_ip())
    monkeypatch.setenv("MONGO_PORT", str(mongo_container.get_exposed_port(27017)))
    monkeypatch.setenv("MONGO_DATABASE", mongo_container.dbname)
    client = mongo_container.get_connection_client()
    yield
    client.drop_database(mongo_container.dbname)
    client.close()


@pytest.fixture()
def blob_storage(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    storage_path = tmp_path_factory.mktemp("local_storage")
    monkeypatch.setenv("Quix__Workspace__Id", "test-workspace")
    monkeypatch.setenv(
        "Quix__BlobStorage__Connection__Json",
        f'''
        {{
            "provider": "local",
            "local_storage": {{
                "DirectoryPath": "{storage_path.absolute()}"
            }}
        }}
        ''',
    )


@pytest.fixture()
def fs(blob_storage: None) -> Any:
    return get_filesystem()


@pytest.fixture(scope="session")
def kafka_container(network: Network) -> Generator[KafkaContainer, None, None]:
    with KafkaContainer(name="test-manager-kafka", network=network) as kafka:
        yield kafka


@pytest.fixture(scope="session")
def config_api_container(
    mongo_container: MongoDbContainer,
    kafka_container: KafkaContainer,
    portal_api_url: str,
    network: Network,
) -> Generator[DockerContainer, None, None]:
    image = "quixcontainerregistry.azurecr.io/dynamicconfigurationservice:latest"
    env = {
        "PORT": CONFIG_API_PORT,
        "Quix__Workspace__Id": "test-workspace",
        "Quix__Portal__Api": portal_api_url,
        "MONGO_USER": mongo_container.username,
        "MONGO_PASSWORD": mongo_container.password,
        "MONGO_HOST": "test-manager-mongo",
        "MONGO_PORT": "27017",
        "MONGO_DATABASE": "configuration",
        "MONGO_COLLECTION": "configurations",
        "KAFKA_BROKER_ADDRESS": "test-manager-kafka:9092",
        "KAFKA_CONSUMER_GROUP": "configuration-api",
        "KAFKA_TOPIC": "config-updates",
    }
    with DockerContainer(
        image,
        name="test-manager-config-api",
        env=env,
        ports=[CONFIG_API_PORT],
        network=network,
    ) as config_api:
        wait_for_logs(config_api, "Uvicorn running", timeout=20, raise_on_exit=True)
        yield config_api


@pytest.fixture()
def config_api(
    config_api_container: DockerContainer,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[httpx.Client, None, None]:
    host = config_api_container.get_container_host_ip()
    port = config_api_container.get_exposed_port(CONFIG_API_PORT)
    url = f"http://{host}:{port}"
    monkeypatch.setenv("CONFIG_API_URL", url)
    monkeypatch.setenv("Quix__Sdk__Token", "test")
    client = httpx.Client(base_url=url, headers={"Authorization": "Bearer test"})

    yield client

    # Cleanup: Delete all configurations after test
    all_configs = client.get("/api/v1/configurations").json()
    for config in all_configs.get("data", []):
        client.delete(f"/api/v1/configurations/{config['id']}")


@pytest.fixture(scope="session")
def influx_container(network: Network) -> Generator[InfluxDbContainer, None, None]:
    env = {
        "INFLUXDB_ADMIN_USER": "test",
        "INFLUXDB_ADMIN_PASSWORD": "test",
    }
    with InfluxDbContainer(
        "influxdb:1.11",
        name="test-manager-influx",
        env=env,
        network=network,
    ) as influx:
        yield influx


@pytest.fixture()
def influx(
    monkeypatch: pytest.MonkeyPatch, influx_container: InfluxDbContainer
) -> Generator[InfluxDBClient, None, None]:
    host = influx_container.get_container_host_ip()
    port = str(influx_container.get_exposed_port(8086))
    user = influx_container.env["INFLUXDB_ADMIN_USER"]
    password = influx_container.env["INFLUXDB_ADMIN_PASSWORD"]
    database = "test_manager"

    monkeypatch.setenv("INFLUXDB_HOST", host)
    monkeypatch.setenv("INFLUXDB_PORT", port)
    monkeypatch.setenv("INFLUXDB_USER", user)
    monkeypatch.setenv("INFLUXDB_PASSWORD", password)

    _client = InfluxDBClient(
        host=host,
        port=port,
        username=user,
        password=password,
        database=database,
    )

    yield _client

    for measurement in _client.get_list_measurements():
        _client.query(f'DROP SERIES FROM "{measurement["name"]}"')
    _client.close()


@pytest.fixture()
def override_settings(
    client: TestClient,
) -> Callable[[int], ContextManager[None]]:
    @contextmanager
    def _override_settings(
        file_signature_expiration_seconds: int,
    ) -> Generator[None, None, None]:
        settings = Settings(  # type: ignore[call-arg]
            file_signature_expiration_seconds=file_signature_expiration_seconds,
        )
        app = client.app
        app.dependency_overrides[get_settings] = lambda: settings  # type: ignore[attr-defined]
        yield
        app.dependency_overrides.clear()  # type: ignore[attr-defined]

    return _override_settings


@pytest.fixture()
def client(
    mongo: None,
    influx: InfluxDBClient,
    blob_storage: None,
    config_api: httpx.Client,
) -> Generator[TestClient, None, None]:
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def create_test(client: TestClient) -> TestFactory:
    def _create_test(**kwargs: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        input_data = {
            "test_id": "test1",
            "campaign_id": "campaign1",
            "sample_id": "sample1",
            "environment_id": "env1",
            "operator": "John Doe",
            "grafana_url": "https://grafana.com",
            "status": "draft",
            "start": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc).isoformat(),
            "end": datetime(2024, 1, 15, 16, 45, 0, tzinfo=timezone.utc).isoformat(),
            "sensors": {
                "T1100": {
                    "mp": "t_A_ODU_out_1",
                    "unit": "°C",
                    "description": "Temperatur 1 Kammer",
                    "sensor_id": "P110884",
                    "type": "AI",
                    "source": "EPE",
                    "csv_col": "AI_T1100",
                }
            },
        }
        input_data.update(kwargs)
        response = client.post("/api/v1/tests", json=input_data)
        assert response.status_code == 200
        return input_data, response.json()

    return _create_test
