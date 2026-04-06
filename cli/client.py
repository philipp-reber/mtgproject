import argparse

from lib.extract import check_status, download_data
from lib.mongo import populate_raw_db
from lib.pipeline import start_docker_containers

def main() -> None:
    parser = argparse.ArgumentParser(description="Magic Data and Pricing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("checkstatus", help="Check if new raw data is available")
    subparsers.add_parser("downloaddata", help="Download the raw bulk data")
    subparsers.add_parser("startdocker", help="Start the Docker containers for this project")
    subparsers.add_parser("populateraw", help="Populate the raw MongoDB container with data")

    args = parser.parse_args()

    match args.command:
        case "checkstatus":
            check_status()
        case "downloaddata":
            download_data()
        case "startdocker":
            start_docker_containers()
        case "populateraw":
            populate_raw_db()
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()