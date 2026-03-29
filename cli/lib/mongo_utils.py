import subprocess
from pathlib import Path
from .general_utils import(
    RAW_PATH,
)

def populate_raw_db() -> None:
    if not RAW_PATH.exists():
        print(f"Raw data file not found: {RAW_PATH}")
        return

    container_path = f"/import/{RAW_PATH.name}"

    # TBD: Once I set a real passwort and Username, I should update this call and make everything more secure
    cmd = [
        "docker",
        "exec",
        "-i",
        "raw-mongo",
        "mongoimport",
        "--host", "localhost",
        "--port", "27017",
        "--username", "root",
        "--password", "rootpassword",
        "--authenticationDatabase", "admin",
        "--db", "raw_scryfall",
        "--collection", "cards",
        "--drop",
        "--file", container_path,
        "--jsonArray"
    ]

    print("Starting mongoimport...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("Import successful")
            print(result.stdout)
        else:
            print("Import failed!")
            print(result.stderr)
    except FileNotFoundError:
        print("Docker not installed")