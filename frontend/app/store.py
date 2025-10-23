import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from .env import get_api_url
from .models import LogbookEntry, Test, TestFile, TestLink, TestStatus
from .utils.exceptions import ObjectNotFound
from .utils.validation import raise_from_422

logger = logging.getLogger(__name__)


class DataStore:
    def __init__(self, api_url: str, request_timeout: float = 30.0):
        if not api_url:
            raise ValueError("api_url cannot be empty")
        self._client = httpx.Client(base_url=api_url, timeout=request_timeout)

    def get_tests(self) -> list[Test]:
        response = self._client.get("/api/v1/tests")
        response.raise_for_status()
        tests = [
            Test(
                test_id=data["test_id"],
                status=TestStatus(data["status"]),
                campaign_id=data["campaign_id"],
                sample_id=data["sample_id"],
                operator=data["operator"],
                environment_id=data["environment_id"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                sensors=data["sensors"],
                links=[TestLink(**link_data) for link_data in data["links"]],
                files={
                    file_id: TestFile(
                        id=file_data["id"],
                        name=file_data["name"],
                        url=file_data["url"],
                        uploaded_at=datetime.fromisoformat(file_data["uploaded_at"]),
                        size=file_data["size"],
                    )
                    for file_id, file_data in data.get("files", {}).items()
                },
                grafana_url=data["grafana_url"],
                start=datetime.fromisoformat(data["start"]) if data["start"] else None,
                end=datetime.fromisoformat(data["end"]) if data["end"] else None,
            )
            for data in response.json()
        ]
        return tests

    def get_test(self, test_id: str) -> Test:
        response = self._client.get(f"/api/v1/tests/{test_id}")
        if response.status_code == 404:
            raise ObjectNotFound(f'Test with id "{test_id}" not found')
        else:
            response.raise_for_status()

        data = response.json()
        test = Test(
            test_id=data["test_id"],
            status=TestStatus(data["status"]),
            campaign_id=data["campaign_id"],
            sample_id=data["sample_id"],
            operator=data["operator"],
            environment_id=data["environment_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            sensors=data["sensors"],
            links=[TestLink(**link_data) for link_data in data["links"]],
            files={
                file_id: TestFile(
                    id=file_data["id"],
                    name=file_data["name"],
                    url=file_data["url"],
                    uploaded_at=datetime.fromisoformat(file_data["uploaded_at"]),
                    size=file_data["size"],
                )
                for file_id, file_data in data.get("files", {}).items()
            },
            grafana_url=data["grafana_url"],
            start=datetime.fromisoformat(data["start"]) if data["start"] else None,
            end=datetime.fromisoformat(data["end"]) if data["end"] else None,
        )
        return test

    def add_test(
        self,
        test_id: str,
        campaign_id: str,
        environment_id: str,
        sample_id: str,
        operator: str,
        sensors: Optional[dict[str, dict[str, Any]]],
        grafana_url: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Test:
        sensors = sensors or {}
        params = {
            "test_id": test_id,
            "campaign_id": campaign_id,
            "environment_id": environment_id,
            "sample_id": sample_id,
            "operator": operator,
            "sensors": sensors,
            "grafana_url": grafana_url,
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        }

        response = self._client.post("/api/v1/tests", json=params)
        if response.status_code == 422:
            # Unprocessable Entity from the API
            logger.debug(f'Add test "{test_id}": validation error', exc_info=True)
            raise_from_422(errors=response.json())
        else:
            logger.debug(f'Add test "{test_id}": server error', exc_info=True)
            response.raise_for_status()

        resp_data = response.json()
        test = Test(
            test_id=resp_data["test_id"],
            status=TestStatus(resp_data["status"]),
            campaign_id=resp_data["test_id"],
            sample_id=resp_data["sample_id"],
            operator=resp_data["operator"],
            environment_id=resp_data["environment_id"],
            created_at=datetime.fromisoformat(resp_data["created_at"]),
            updated_at=datetime.fromisoformat(resp_data["updated_at"]),
            sensors=resp_data["sensors"],
            links=[TestLink(**link_data) for link_data in resp_data["links"]],
            files={
                file_id: TestFile(
                    id=file_data["id"],
                    name=file_data["name"],
                    url=file_data["url"],
                    uploaded_at=datetime.fromisoformat(file_data["uploaded_at"]),
                    size=file_data["size"],
                )
                for file_id, file_data in resp_data.get("files", {}).items()
            },
            grafana_url=resp_data["grafana_url"],
            start=datetime.fromisoformat(resp_data["start"])
            if resp_data["start"]
            else None,
            end=datetime.fromisoformat(resp_data["end"]) if resp_data["end"] else None,
        )
        return test

    def edit_test(
        self,
        test_id: str,
        campaign_id: str,
        environment_id: str,
        sample_id: str,
        operator: str,
        sensors: Optional[dict[str, dict[str, Any]]],
        grafana_url: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Test:
        sensors = sensors or {}
        params = {
            "campaign_id": campaign_id,
            "environment_id": environment_id,
            "sample_id": sample_id,
            "operator": operator,
            "sensors": sensors,
            "grafana_url": grafana_url,
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        }

        response = self._client.put(f"/api/v1/tests/{test_id}", json=params)
        if response.status_code == 422:
            # Unprocessable Entity from the API
            logger.debug(f'Edit test "{test_id}": validation error', exc_info=True)
            raise_from_422(errors=response.json())
        elif response.status_code == 404:
            raise ObjectNotFound(f'Test with id "{test_id}" not found')
        else:
            logger.debug(f'Edit test "{test_id}": server error', exc_info=True)
            response.raise_for_status()

        resp_data = response.json()
        test = Test(
            test_id=resp_data["test_id"],
            status=TestStatus(resp_data["status"]),
            campaign_id=resp_data["test_id"],
            sample_id=resp_data["sample_id"],
            operator=resp_data["operator"],
            environment_id=resp_data["environment_id"],
            created_at=datetime.fromisoformat(resp_data["created_at"]),
            updated_at=datetime.fromisoformat(resp_data["updated_at"]),
            sensors=resp_data["sensors"],
            links=[TestLink(**link_data) for link_data in resp_data["links"]],
            files={
                file_id: TestFile(
                    id=file_data["id"],
                    name=file_data["name"],
                    url=file_data["url"],
                    uploaded_at=datetime.fromisoformat(file_data["uploaded_at"]),
                    size=file_data["size"],
                )
                for file_id, file_data in resp_data.get("files", {}).items()
            },
            grafana_url=resp_data["grafana_url"],
            start=datetime.fromisoformat(resp_data["start"])
            if resp_data["start"]
            else None,
            end=datetime.fromisoformat(resp_data["end"]) if resp_data["end"] else None,
        )
        return test

    def delete_test(self, test_id: str) -> None:
        response = self._client.delete(f"/api/v1/tests/{test_id}")
        if response.status_code == 404:
            raise ObjectNotFound(f'Test with id "{test_id}" not found')
        else:
            response.raise_for_status()

    def get_file_upload_url(self, test_id: str, filename: str) -> str:
        response = self._client.post(
            f"/api/v1/tests/{test_id}/files", json={"filename": filename}
        )
        response.raise_for_status()
        # Force HTTPS here
        url = response.json()["url"].replace("http://", "https://")
        return url

    def delete_test_file(self, test_id: str, file_id: str):
        response = self._client.delete(f"/api/v1/tests/{test_id}/files/{file_id}")
        if response.status_code == 404:
            raise ObjectNotFound(f'File with id "{file_id}" not found')
        else:
            response.raise_for_status()

    def get_file_download_url(self, test_id: str, file_id: str) -> str:
        return str(
            self._client.base_url.join(
                f"/api/v1/tests/{test_id}/files/{file_id}/download"
            )
        )

    def add_logbook_entry(
        self,
        test_id: str,
        operator: str,
        content: str,
        timestamp: datetime,
        sensor_ids: list[str] = (),
    ) -> LogbookEntry:
        params = {
            "operator": operator,
            "content": content,
            "timestamp": timestamp.isoformat(),
            "sensor_ids": sensor_ids,
        }

        response = self._client.post(f"/api/v1/tests/{test_id}/logbook", json=params)
        if response.status_code == 422:
            # Unprocessable Entity from the API
            logger.debug(
                f'Add logbook entry for test "{test_id}": validation error',
                exc_info=True,
            )
            raise_from_422(errors=response.json())
        else:
            logger.debug(
                f'Add logbook entry for test "{test_id}": server error', exc_info=True
            )
            response.raise_for_status()

        resp_data = response.json()
        entry = LogbookEntry(
            id=resp_data["test_id"],
            test_id=resp_data["test_id"],
            operator=resp_data["operator"],
            sensor_ids=resp_data.get("sensor_ids", []),
            content=resp_data["content"],
            timestamp=datetime.fromisoformat(resp_data["timestamp"]),
        )
        return entry

    def get_logbook_entries(
        self,
        test_id: str,
    ) -> list[LogbookEntry]:
        response = self._client.get(f"/api/v1/tests/{test_id}/logbook")
        response.raise_for_status()

        entries = [
            LogbookEntry(
                id=data["id"],
                test_id=data["test_id"],
                operator=data["operator"],
                sensor_ids=data.get("sensor_ids", []),
                content=data["content"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
            for data in response.json()
        ]
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries

    def update_logbook_entry(
        self,
        test_id: str,
        entry_id: str,
        operator: str,
        content: str,
        timestamp: datetime,
        sensor_ids: list[str] = (),
    ) -> LogbookEntry:
        params = {
            "operator": operator,
            "content": content,
            "timestamp": timestamp.isoformat(),
            "sensor_ids": sensor_ids,
        }

        response = self._client.put(
            f"/api/v1/tests/{test_id}/logbook/{entry_id}", json=params
        )
        if response.status_code == 422:
            # Unprocessable Entity from the API
            logger.debug(
                f'Edit logbook entry "{entry_id}": validation error', exc_info=True
            )
            raise_from_422(errors=response.json())
        elif response.status_code == 404:
            raise ObjectNotFound(
                f'Logbook entry "{entry_id}" for Test "{test_id}" not found'
            )
        else:
            logger.debug(
                f'Edit logbook entry "{entry_id}": server error', exc_info=True
            )
            response.raise_for_status()

        resp_data = response.json()
        entry = LogbookEntry(
            id=resp_data["id"],
            test_id=resp_data["test_id"],
            operator=resp_data["operator"],
            sensor_ids=resp_data.get("sensor_ids", []),
            content=resp_data["content"],
            timestamp=datetime.fromisoformat(resp_data["timestamp"]),
        )
        return entry

    def get_logbook_entry(self, test_id: str, entry_id: str) -> LogbookEntry:
        response = self._client.get(f"/api/v1/tests/{test_id}/logbook/{entry_id}")
        if response.status_code == 404:
            raise ObjectNotFound(
                f'Logbook entry "{entry_id}" for Test "{test_id}" not found'
            )
        else:
            response.raise_for_status()

        data = response.json()
        entry = LogbookEntry(
            id=data["id"],
            test_id=data["test_id"],
            operator=data["operator"],
            sensor_ids=data.get("sensor_ids", []),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
        return entry

    def delete_logbook_entry(
        self,
        test_id: str,
        entry_id: str,
    ) -> None:
        response = self._client.delete(f"/api/v1/tests/{test_id}/logbook/{entry_id}")
        if response.status_code == 404:
            raise ObjectNotFound(
                f'Logbook entry "{entry_id}" for Test "{test_id}" not found'
            )
        else:
            response.raise_for_status()


STORE = DataStore(api_url=get_api_url())
