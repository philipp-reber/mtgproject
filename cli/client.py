import argparse

from lib.extract import check_status, download_data
from lib.mongo import populate_raw_db, get_random_card, get_card_by_name
from lib.pipeline import start_docker_containers
from lib.transform import transform_card

def main() -> None:
    parser = argparse.ArgumentParser(description="Magic Data and Pricing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("checkstatus", help="Check if new raw data is available")
    subparsers.add_parser("downloaddata", help="Download the raw bulk data")
    subparsers.add_parser("startdocker", help="Start the Docker containers for this project")
    subparsers.add_parser("populateraw", help="Populate the raw MongoDB container with data")
    tarnsform_parser = subparsers.add_parser("transformcard", help="Transform a random card and print the output dictionary for testing")
    tarnsform_parser.add_argument("cardname", type=str, nargs="?", default="", help="Cardname to transform")

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
        case "transformcard":
            if args.cardname:
                card = get_card_by_name(args.cardname)
            else:
                card = get_random_card()
            print(transform_card(card))
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()