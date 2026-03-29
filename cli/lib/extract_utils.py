# Utility Functions for checking, downloading and updating the raw data.
import json
import requests
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from .general_utils import(
    RAW_PATH,
    BULK_DATA_URL,
    RAW_META_PATH,
)

def check_status() -> None:
    print("Checking Raw Data Version...")

    if not RAW_META_PATH.exists():
        print("No Metadata found, try to freshly download the data with the command: downloaddata")
        return
    else:
        with RAW_META_PATH.open("r", encoding="utf-8") as f:
            metadata = json.load(f)

        all_cards_updated = next(item for item in metadata["data"] if item["type"] == "all_cards")
        local_updated = datetime.fromisoformat(all_cards_updated["updated_at"].replace("Z", "+00:00"))

        resp = requests.get(BULK_DATA_URL)
        resp.raise_for_status()
        remote_data = resp.json()["data"]
        all_cards = next(item for item in remote_data if item["type"] == "all_cards")
        remote_updated = datetime.fromisoformat(all_cards["updated_at"].replace("Z", "+00:00"))

        print("Remote version:", remote_updated)
        print("Local version:", local_updated)
        if remote_updated > local_updated:
            print("Your data is outdated!")
            print("Download new version with the command: downloaddata")
        else:
            print("Your data is up-to-date!")
    
    print("Checking Raw Database...")

    try:
        client = MongoClient(
            host="127.0.0.1",
            port=27017,
            username="root",
            password="rootpassword",
            authSource="admin",
            serverSelectionTimeoutMS=2000
        )

        client.admin.command("ping")
        print("Database for Raw data is up and running")

    except ServerSelectionTimeoutError:
        print("Database is not running, start it up by running the following command: startdocker")
        return
    
    print("Checking Raw Database for contents...")
    db = client["raw_scryfall"]
    card = db["cards"].find_one({}, {"name": 1})

    if card:
        print(f"Found a card in the database: {card}")
    else:
        print("Database is empty, run the following command to populate it with raw data: populateraw")

def download_data():
    RAW_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    meta_resp = requests.get(BULK_DATA_URL)
    meta_resp.raise_for_status()
    metadata = meta_resp.json()
    with RAW_META_PATH.open("w", encoding="utf-8") as f:
        json.dump(metadata, f,)
    all_cards = next(item for item in metadata["data"] if item["type"] == "all_cards")
    download_url = all_cards["download_uri"]

    with requests.get(download_url, stream=True) as resp:
        resp.raise_for_status()
        total_size = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024

        with RAW_PATH.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)

                if total_size:
                    percent = downloaded / total_size * 100
                    print(f"\rDownloading: {percent:.1f}%", end="")
                else:
                    mb = downloaded / (1024 * 1024)
                    print(f"\rDownloaded: {mb:.1f} MB", end="")
                    
        print("\nDownload complete.")