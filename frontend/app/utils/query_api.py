import httpx
import logging
import json
import csv
import io
from typing import Any, Tuple
from app.env import SDK_TOKEN, get_lake_query_ui_url

logger = logging.getLogger(__name__)


async def download_test_data(campaign_id: str, environment_id: str, test_id: str):
    """
    Send a POST request to the Quix query API to download test data.
    
    Args:
        campaign_id: The campaign ID
        environment_id: The environment ID
        test_id: The test ID
        
    Returns:
        The response data from the API
    """
    if not SDK_TOKEN:
        raise ValueError("Quix SDK token is not configured. Please set the Quix__Sdk__Token environment variable.")
    
    url = f"{get_lake_query_ui_url()}/api/query"
    logger.info(f"Query URL: {url}")
    
    # Build the SQL query
    query = f"SELECT * FROM config-enriched-data WHERE campaign_id = '{campaign_id}' AND environment_id = '{environment_id}' AND test_id = '{test_id}'"
    logger.info(f"SQL Query: {query}")
    
    headers = {
        "Authorization": f"Bearer {SDK_TOKEN}",
        "Content-Type": "text/plain"
    }
    logger.info(f"Headers: Authorization: Bearer {SDK_TOKEN[:10]}..., Content-Type: text/plain")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                content=query,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            # Try to parse as JSON, otherwise return text
            try:
                return response.json()
            except:
                return response.text
    except httpx.HTTPError as e:
        logger.error(f"Error downloading test data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error downloading test data: {e}")
        raise


def format_data_for_download(data: Any, test_id: str) -> Tuple[str, str, str]:
    """
    Format the data for download and determine the appropriate file format.
    
    Args:
        data: The data to format
        test_id: The test ID for the filename
        
    Returns:
        Tuple of (content, filename, mime_type)
    """
    if isinstance(data, list) and len(data) > 0:
        # Convert to CSV if we have a list of dictionaries
        if isinstance(data[0], dict):
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            content = output.getvalue()
            filename = f"test_data_{test_id}.csv"
            mime_type = "text/csv"
        else:
            # Otherwise save as JSON
            content = json.dumps(data, indent=2)
            filename = f"test_data_{test_id}.json"
            mime_type = "application/json"
    elif isinstance(data, dict):
        # Save dictionary as JSON
        content = json.dumps(data, indent=2)
        filename = f"test_data_{test_id}.json"
        mime_type = "application/json"
    else:
        # Save raw data as text
        content = str(data)
        filename = f"test_data_{test_id}.txt"
        mime_type = "text/plain"
    
    return content, filename, mime_type
