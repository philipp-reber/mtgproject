import argparse

from lib.extract_utils import(
    check_status,
    download_data,
)
from lib.mongo_utils import(
    populate_raw_db,
)

from lib.general_utils import(
    start_docker_containers,
)

def main() -> None:
    parser = argparse.ArgumentParser(description="Magic Data and Pricing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("checkstatus", help="Check if new raw data is available")
    subparsers.add_parser("downloaddata", help="Download the raw bulk data")
    subparsers.add_parser("startdocker", help="Starts the docker containers for this project through the compose file")
    subparsers.add_parser("populateraw", help="Populates the raw MongoDB Container with data")

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