# Utility Functions for checking, downloading and updating the raw data.
import json
from datetime import datetime

import requests
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from .config import mongo, paths, scryfall


def check_status() -> None:
    print("Checking raw data version...")

    if not paths.raw_meta_path.exists():
        print("No metadata found. Download the data first with: downloaddata")
        return

    with paths.raw_meta_path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    local_all_cards = next(item for item in metadata["data"] if item["type"] == "all_cards")
    local_updated = datetime.fromisoformat(local_all_cards["updated_at"].replace("Z", "+00:00"))

    response = requests.get(scryfall.bulk_data_url, timeout=30)
    response.raise_for_status()
    remote_metadata = response.json()

    remote_all_cards = next(item for item in remote_metadata["data"] if item["type"] == "all_cards")
    remote_updated = datetime.fromisoformat(remote_all_cards["updated_at"].replace("Z", "+00:00"))

    print(f"Remote version: {remote_updated}")
    print(f"Local version:  {local_updated}")

    if remote_updated > local_updated:
        print("Your local raw data is outdated.")
        print("Download the new version with: downloaddata")
    else:
        print("Your raw data is up to date.")

    print("Checking raw MongoDB container...")

    try:
        client = MongoClient(
            host=mongo.host,
            port=mongo.port,
            username=mongo.username,
            password=mongo.password,
            authSource=mongo.auth_source,
            serverSelectionTimeoutMS=mongo.server_selection_timeout_ms,
        )

        client.admin.command("ping")
        print("MongoDB is running.")

    except ServerSelectionTimeoutError:
        print("MongoDB is not running. Start the containers with: startdocker")
        return

    print("Checking raw database for contents...")

    db = client[mongo.database]
    card = db[mongo.collection].find_one({}, {"name": 1})

    if card:
        print(f"Found a card in the database: {card}")
    else:
        print("The database is empty. Populate it with: populateraw")


def download_data() -> None:
    paths.raw_meta_path.parent.mkdir(parents=True, exist_ok=True)
    paths.raw_data_path.parent.mkdir(parents=True, exist_ok=True)

    print("Downloading bulk metadata...")

    meta_response = requests.get(scryfall.bulk_data_url, timeout=30)
    meta_response.raise_for_status()
    metadata = meta_response.json()

    with paths.raw_meta_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    all_cards = next(item for item in metadata["data"] if item["type"] == "all_cards")
    download_url = all_cards["download_uri"]

    print("Downloading all_cards dataset...")

    with requests.get(download_url, stream=True, timeout=60) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024

        with paths.raw_data_path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue

                file.write(chunk)
                downloaded += len(chunk)

                if total_size:
                    percent = downloaded / total_size * 100
                    print(f"\rDownloading: {percent:.1f}%", end="")
                else:
                    mb_downloaded = downloaded / (1024 * 1024)
                    print(f"\rDownloaded: {mb_downloaded:.1f} MB", end="")

    print("\nDownload complete.")