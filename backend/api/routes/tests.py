from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException
from pymongo import ReturnDocument
from pymongo.database import Database
from quixportal import get_filesystem

from ..auth import update_permission, read_permission
from ..mongo import get_mongo
from ..influx import Influx, get_influx
from ..config_api import get_config_api_client
from ..models import Test, TestCreate, TestQuery, TestUpdate
from ..settings import Settings, get_settings

router = APIRouter()


@router.post("/tests", response_model=Test, response_model_by_alias=False)
def create_test(
    test_data: TestCreate = Body(...),
    mongo: Database[dict[str, Any]] = Depends(get_mongo),
    config_api: httpx.Client = Depends(get_config_api_client),
    _: None = Depends(update_permission),
) -> Test:
    if mongo.tests.find_one({"_id": test_data.test_id}):
        raise HTTPException(status_code=409, detail="Test with this ID already exists")

    response = config_api.post(
        "/api/v1/configurations",
        json={
            "metadata": {"type": "TestConfig", "target_key": test_data.test_id},
            "content": {
                "test_id": test_data.test_id,
                "campaign_id": test_data.campaign_id,
                "sample_id": test_data.sample_id,
                "environment_id": test_data.environment_id,
                "operator": test_data.operator,
                "sensors": test_data.sensors,
            },
        },
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=424,
            detail=f"Failed to create configuration: {e.response.status_code} {e.response.text}",
        )
    config_id = response.json()["data"]["id"]

    test = Test(
        _id=test_data.test_id,
        config_id=config_id,
        **test_data.model_dump(exclude={"test_id"}),
    )
    mongo.tests.insert_one(test.model_dump(by_alias=True))
    return test


@router.get("/tests", response_model=list[Test], response_model_by_alias=False)
def list_tests(
    query_params: TestQuery = Depends(),
    mongo: Database[dict[str, Any]] = Depends(get_mongo),
    _: None = Depends(read_permission),
) -> list[Test]:
    query = query_params.model_dump(exclude_none=True, exclude={"q"})
    if "test_id" in query:
        query["_id"] = query.pop("test_id")
    if query_params.q:
        query["$text"] = {"$search": query_params.q}

    return [Test(**test) for test in mongo.tests.find(query)]


@router.get("/tests/{test_id}", response_model=Test, response_model_by_alias=False)
def get_test(
    test_id: str,
    mongo: Database[dict[str, Any]] = Depends(get_mongo),
    _: None = Depends(read_permission),
) -> Test:
    """
    Retrieves a single test by its test_id.
    """
    if not (test := mongo.tests.find_one({"_id": test_id})):
        raise HTTPException(status_code=404, detail="Test not found")
    return Test(**test)


@router.put("/tests/{test_id}", response_model=Test, response_model_by_alias=False)
def update_test(
    test_id: str,
    test_update: TestUpdate,
    mongo: Database[dict[str, Any]] = Depends(get_mongo),
    config_api: httpx.Client = Depends(get_config_api_client),
    _: None = Depends(update_permission),
) -> Test:
    """
    Updates the metadata of a single test.
    """
    update_data = test_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="At least one field must be provided for update",
        )

    update_data["updated_at"] = datetime.now(timezone.utc)

    if not (
        updated_test := mongo.tests.find_one_and_update(
            {"_id": test_id},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER,
        )
    ):
        raise HTTPException(status_code=404, detail="Test not found")

    test = Test(**updated_test)

    response = config_api.put(
        f"/api/v1/configurations/{test.config_id}",
        json={
            "content": {
                "test_id": test.test_id,
                "campaign_id": test.campaign_id,
                "sample_id": test.sample_id,
                "environment_id": test.environment_id,
                "operator": test.operator,
                "sensors": test.sensors,
            },
        },
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=424,
            detail=f"Failed to update configuration: {e.response.status_code} {e.response.text}",
        )

    return test


@router.delete("/tests/{test_id}", status_code=204)
def delete_test(
    test_id: str,
    mongo: Database[dict[str, Any]] = Depends(get_mongo),
    fs: Any = Depends(get_filesystem),
    settings: Settings = Depends(get_settings),
    influx: Influx = Depends(get_influx),
    config_api: httpx.Client = Depends(get_config_api_client),
    _: None = Depends(update_permission),
) -> None:
    """
    Deletes a single test by its test_id.
    """
    # Get the test to find associated files
    if not (test := mongo.tests.find_one({"_id": test_id})):
        raise HTTPException(status_code=404, detail="Test not found")

    # Delete configuration from Config API
    response = config_api.delete(f"/api/v1/configurations/{test['config_id']}")
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=424,
            detail=f"Failed to delete configuration: {e.response.status_code} {e.response.text}",
        )

    # Delete all files from blob storage
    files = test.get("files", {})
    for file in files.values():
        path = f"{settings.workspace_id}/test-manager/{test_id}/{file['name']}"
        try:
            fs.rm_file(path)
        except FileNotFoundError:
            pass

    # Delete logbook entries from InfluxDB
    logbook_entries = list(mongo.logbook.find({"test_id": test_id}))
    for entry in logbook_entries:
        influx.logbook.delete(entry["_id"])

    # Delete logbook entries and test from MongoDB
    mongo.logbook.delete_many({"test_id": test_id})
    mongo.tests.delete_one({"_id": test_id})
