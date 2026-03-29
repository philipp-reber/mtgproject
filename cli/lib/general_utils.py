from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "scryfall_all_cards.json"
RAW_META_PATH = PROJECT_ROOT / "data" / "raw" / "scryfall_all_cards.meta.json"
BULK_DATA_URL = "https://api.scryfall.com/bulk-data"
DOCKER_COMPOSE_PATH = PROJECT_ROOT / "docker" / "docker-compose.yml"

def start_docker_containers() -> None:
    cmd = [
        "docker",
        "compose",
        "-f",
        "docker/docker-compose.yml",
        "up",
        "-d"
    ]

    print("Starting Docker containers...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("Docker containers started")
            print(result.stdout)
        else:
            print("Failed to start Docker containers")
            print(result.stderr)
    except FileNotFoundError:
        print("Docker is not installed")