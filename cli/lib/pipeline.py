import subprocess

from .config import paths

def start_docker_containers() -> None:
    command = [
        "docker",
        "compose",
        "--env-file",
        str(paths.project_root / ".env"),
        "-f",
        str(paths.docker_compose_path),
        "up",
        "-d",
    ]

    print("Starting Docker containers...")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=paths.project_root,
        )

        if result.returncode == 0:
            print("Docker containers started successfully.")
            print(result.stdout)
        else:
            print("Failed to start Docker containers.")
            print(result.stderr)

    except FileNotFoundError:
        print("Docker is not installed or not available in PATH.")