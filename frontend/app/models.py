import dataclasses
import enum
from datetime import datetime
from typing import Any, Optional


@dataclasses.dataclass(kw_only=True)
class TestFile:
    id: str
    name: str
    url: str
    uploaded_at: datetime
    size: int


@dataclasses.dataclass(kw_only=True)
class TestLink:
    id: str
    url: str
    label: str


class TestStatus(enum.StrEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

    @property
    def label(self) -> str:
        if self == self.FINISHED:
            return "Finished"
        elif self == self.IN_PROGRESS:
            return "In progress"
        else:
            return "Draft"


@dataclasses.dataclass(kw_only=True)
class Test:
    test_id: str
    environment_id: str
    campaign_id: str
    sample_id: str
    operator: str
    created_at: datetime
    updated_at: datetime
    status: TestStatus
    files: dict[str, TestFile] = dataclasses.field(default_factory=dict)
    sensors: dict[str, dict[str, Any]] = dataclasses.field(default_factory=dict)
    links: list[TestLink] = dataclasses.field(default_factory=list)
    grafana_url: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None


@dataclasses.dataclass(kw_only=True)
class LogbookEntry:
    id: str
    test_id: str
    operator: str
    content: str
    timestamp: datetime
    sensor_ids: list[str] = dataclasses.field(default_factory=list)
