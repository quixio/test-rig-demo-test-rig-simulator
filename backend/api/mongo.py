from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from .settings import MongoSettings

_mongo: Database[dict[str, Any]]


def connect(settings: MongoSettings) -> None:
    global _mongo
    _mongo = MongoClient(
        settings.url,
        tz_aware=True,
        uuidRepresentation="standard",
    ).get_database(settings.database)

    # Create indexes for optimal query performance
    _mongo.tests.create_index("campaign_id")
    _mongo.tests.create_index("sample_id")
    _mongo.tests.create_index("environment_id")
    _mongo.tests.create_index("operator")
    _mongo.tests.create_index("status")

    # Create text index for full-text search across multiple fields
    _mongo.tests.create_index(
        [
            ("test_id", "text"),
            ("campaign_id", "text"),
            ("sample_id", "text"),
            ("environment_id", "text"),
            ("operator", "text"),
            ("description", "text"),
        ]
    )

    _mongo.logbook.create_index("test_id")


def disconnect() -> None:
    _mongo.client.close()


def get_mongo() -> Database[dict[str, Any]]:
    return _mongo
