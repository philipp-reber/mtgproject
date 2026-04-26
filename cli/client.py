import argparse

from lib.extract import check_status, download_data
from lib.mongo import populate_raw_db, get_random_card, get_card_by_name
from lib.pipeline import start_docker_containers
from lib.transform import transform_card
from lib.postgres import get_connection, load_transformed_card

def main() -> None:
    parser = argparse.ArgumentParser(description="Magic Data and Pricing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("checkstatus", help="Check if new raw data is available")
    subparsers.add_parser("downloaddata", help="Download the raw bulk data")
    subparsers.add_parser("startdocker", help="Start the Docker containers for this project")
    subparsers.add_parser("populateraw", help="Populate the raw MongoDB container with data")

    transform_parser = subparsers.add_parser("transformcard", help="Transform a card and print the output dictionary")
    transform_parser.add_argument("cardname", type=str, nargs="?", default="", help="Cardname to transform")

    subparsers.add_parser("loadtestcard", help="Insert a random card into Postgres and query it")

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

        case "loadtestcard":
            # 1. Get random card from Mongo
            raw_card = get_random_card()

            if not raw_card:
                print("No card found in MongoDB")
                return

            print(f"Inserting card: {raw_card.get('name')}")

            # 2. Transform
            transformed = transform_card(raw_card)

            # 3. Insert into Postgres
            conn = get_connection()
            try:
                load_transformed_card(conn, transformed)

                # 4. Query it back
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT card_id, card_name
                        FROM fact_cards
                        WHERE card_id = %s;
                        """,
                        (transformed["card"]["card_id"],),
                    )

                    result = cur.fetchone()

                    if result:
                        print("Inserted & fetched from Postgres:")
                        print(f"card_id={result[0]}, card_name={result[1]}")
                        cur.execute("SELECT COUNT(*) FROM dim_type_line;")
                        print("dim_type_line rows:", cur.fetchone()[0]) # type: ignore
                    else:
                        print("Card not found in Postgres after insert (unexpected)")

            finally:
                conn.close()
        case _:
            parser.print_help()

if __name__ == "__main__":
    main()