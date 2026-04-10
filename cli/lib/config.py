from __future__ import annotations # to make sure the decorator works as intended

import os
from dataclasses import dataclass # decoartor to simplify writing classes which store structured data
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def get_env(name: str, default: str | None = None) -> str:
    # Standardizing Env variable behaviour and allowing standards
    value = os.getenv(name)

    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(f"Environment variable '{name}' is missing and no default was provided.")

    return value


def get_env_int(name: str, default: int | None = None) -> int:
    # necessary to get int values properly from the .env file
    raw_value = os.getenv(name)

    if raw_value is None or raw_value == "":
        if default is not None:
            return default
        raise ValueError(f"Environment variable '{name}' is missing and no default was provided.")

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable '{name}' must be an integer, got '{raw_value}'."
        ) from exc


@dataclass(frozen=True)
class PathConfig:
    project_root: Path
    data_dir: Path
    raw_dir: Path
    raw_data_path: Path
    raw_meta_path: Path
    docker_dir: Path
    docker_compose_path: Path


@dataclass(frozen=True)
class ScryfallConfig:
    bulk_data_url: str


@dataclass(frozen=True)
class MongoConfig:
    host: str
    port: int
    username: str
    password: str
    auth_source: str
    database: str
    collection: str
    container_name: str
    import_mount_path: str
    server_selection_timeout_ms: int

    @property
    def uri(self) -> str:
        return (
            f"mongodb://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/?authSource={self.auth_source}"
        )


@dataclass(frozen=True)
class PostgresConfig:
    host: str
    port: int
    username: str
    password: str
    database: str
    container_name: str

    @property
    def uri(self) -> str:
        return (
            f"postgresql://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

@dataclass(frozen=True)
class PipelineConfig:
    batch_size: int

# Instantiation section

paths = PathConfig(
    project_root=PROJECT_ROOT,
    data_dir=PROJECT_ROOT / "data",
    raw_dir=PROJECT_ROOT / "data" / "raw",
    raw_data_path=PROJECT_ROOT / "data" / "raw" / "scryfall_all_cards.json",
    raw_meta_path=PROJECT_ROOT / "data" / "raw" / "scryfall_all_cards.meta.json",
    docker_dir=PROJECT_ROOT / "docker",
    docker_compose_path=PROJECT_ROOT / "docker" / "docker-compose.yml",
)

scryfall = ScryfallConfig(
    bulk_data_url=get_env("SCRYFALL_BULK_DATA_URL", "https://api.scryfall.com/bulk-data"),
)

mongo = MongoConfig(
    host=get_env("MONGO_HOST", "127.0.0.1"),
    port=get_env_int("MONGO_PORT", 27017),
    username=get_env("MONGO_USERNAME"),
    password=get_env("MONGO_PASSWORD"),
    auth_source=get_env("MONGO_AUTH_SOURCE"),
    database=get_env("MONGO_DATABASE", "raw_scryfall"),
    collection=get_env("MONGO_COLLECTION", "cards"),
    container_name=get_env("MONGO_CONTAINER_NAME", "raw-mongo"),
    import_mount_path=get_env("MONGO_IMPORT_MOUNT_PATH", "/import"),
    server_selection_timeout_ms=get_env_int("MONGO_TIMEOUT_MS", 2000),
)

postgres = PostgresConfig(
    host=get_env("POSTGRES_HOST", "127.0.0.1"),
    port=get_env_int("POSTGRES_PORT", 5432),
    username=get_env("POSTGRES_USER"),
    password=get_env("POSTGRES_PASSWORD"),
    database=get_env("POSTGRES_DB", "bdv_scryfall"),
    container_name=get_env("POSTGRES_CONTAINER_NAME", "bdv-postgres"),
)

pipeline = PipelineConfig(
    batch_size=get_env_int("PIPELINE_BATCH_SIZE", 1000),
)




















import subprocess

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