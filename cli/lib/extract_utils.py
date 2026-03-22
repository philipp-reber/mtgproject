# Utility Functions for checking, downloading and updating the raw data.
import json
import requests
from datetime import datetime
from .general_utils import(
    RAW_PATH,
    BULK_DATA_URL,
    RAW_META_PATH,
)

def check_data_updates() -> None:
    
    if not RAW_META_PATH.exists():
        print("No Metadata found, try to freshly download the data")
        return
    with RAW_META_PATH.open("r") as f:
        metadata = json.load(f)
    all_cards_updated = next(item for item in metadata["data"] if item["type"] == "all_cards")
    local_updated = datetime.fromisoformat(all_cards_updated["updated_at"].replace("Z", "+00:00"))

    resp = requests.get(BULK_DATA_URL)
    remote_data = resp.json()["data"]
    all_cards = next(item for item in remote_data if item["type"] == "all_cards")
    remote_updated = datetime.fromisoformat(all_cards["updated_at"].replace("Z", "+00:00"))

    print("Remote version:", remote_updated)
    print("Local version:", local_updated)

def download_data():
    pass