import argparse

from lib.extract_utils import(
    check_data_updates,
)

def main() -> None:
    parser = argparse.ArgumentParser(description="Magic Data and Pricing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("checkupdates", help="Check if new raw data is available")

    args = parser.parse_args()

    match args.command:
        case "checkupdates":
            check_data_updates()
        case _:
            parser.print_help()

if __name__ == "__main__":
    main()