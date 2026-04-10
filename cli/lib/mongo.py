import subprocess
from pymongo import MongoClient

from .config import mongo, paths


def populate_raw_db() -> None:
    if not paths.raw_data_path.exists():
        print(f"Raw data file not found: {paths.raw_data_path}")
        return

    container_path = f"{mongo.import_mount_path}/{paths.raw_data_path.name}"

    command = [
        "docker",
        "exec",
        "-i",
        mongo.container_name,
        "mongoimport",
        "--host", "localhost",
        "--port", str(mongo.port),
        "--username", mongo.username,
        "--password", mongo.password,
        "--authenticationDatabase", mongo.auth_source,
        "--db", mongo.database,
        "--collection", mongo.collection,
        "--drop",
        "--file", container_path,
        "--jsonArray",
    ]

    print("Starting mongoimport...")

    try:
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print("Import successful.")
            print(result.stdout)
        else:
            print("Import failed.")
            print(result.stderr)

    except FileNotFoundError:
        print("Docker is not installed or not available in PATH.")

def get_random_card() -> dict:
    client = MongoClient(
        host=mongo.host,
        port=mongo.port,
        username=mongo.username,
        password=mongo.password,
        authSource=mongo.auth_source,
        serverSelectionTimeoutMS=mongo.server_selection_timeout_ms,
    )
    db = client[mongo.database]
    result = list(db[mongo.collection].aggregate([
        {"$sample": {"size": 1}}
    ]))

    if not result:
        raise ValueError("No documents found in collection")

    return result[0]