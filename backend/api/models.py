from datetime import datetime
from typing import Any
from enum import Enum

from pydantic import BaseModel, Field

from .utils import now


class TestStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class File(BaseModel):
    """Represents a file in blob storage."""

    id: str
    name: str
    url: str
    size: int
    uploaded_at: datetime = Field(default_factory=now)


class PresignedUploadResponse(BaseModel):
    url: str


class PresignedUploadRequest(BaseModel):
    filename: str


class Link(BaseModel):
    """Represents an external link."""

    id: str
    url: str
    label: str


class LinkCreate(BaseModel):
    """Represents the data to create a link."""

    url: str
    label: str


class Test(BaseModel):
    """Represents a single test record in the database."""

    test_id: str = Field(..., alias="_id")
    campaign_id: str
    sample_id: str
    environment_id: str
    operator: str
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
    sensors: dict[str, dict[str, Any]]
    config_id: str
    links: list[Link] = Field(default_factory=list)
    files: dict[str, File] = Field(default_factory=dict)
    grafana_url: str | None = None
    status: TestStatus = TestStatus.DRAFT
    start: datetime | None = None
    end: datetime | None = None


class TestCreate(BaseModel):
    """Represents the data required to create a test."""

    test_id: str
    campaign_id: str
    sample_id: str
    environment_id: str
    operator: str
    sensors: dict[str, dict[str, Any]]
    grafana_url: str | None = None
    status: TestStatus = TestStatus.DRAFT
    start: datetime | None = None
    end: datetime | None = None


class TestUpdate(BaseModel):
    """Represents the updatable fields of a test."""

    campaign_id: str | None = None
    sample_id: str | None = None
    environment_id: str | None = None
    operator: str | None = None
    sensors: dict[str, dict[str, Any]] | None = None
    grafana_url: str | None = None
    status: TestStatus | None = None
    start: datetime | None = None
    end: datetime | None = None


class TestQuery(BaseModel):
    """Defines the available query parameters for filtering tests."""

    test_id: str | None = None
    campaign_id: str | None = None
    sample_id: str | None = None
    environment_id: str | None = None
    operator: str | None = None
    status: TestStatus | None = None
    q: str | None = None


class LogbookEntry(BaseModel):
    """Represents a single logbook entry for a test."""

    id: str = Field(..., alias="_id")
    test_id: str
    created_at: datetime = Field(default_factory=now)
    timestamp: datetime = Field(default_factory=now)
    operator: str
    content: str
    sensor_ids: list[str] = []


class LogbookEntryCreate(BaseModel):
    """Represents the data required to create a logbook entry."""

    operator: str
    content: str
    sensor_ids: list[str] = []
    timestamp: datetime = Field(default_factory=now)


class LogbookEntryUpdate(BaseModel):
    """Represents the updatable fields of a logbook entry."""

    operator: str | None = None
    content: str | None = None
    sensor_ids: list[str] | None = None
    timestamp: datetime | None = None
