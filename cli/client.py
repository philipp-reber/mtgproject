# client.py
import argparse

from lib.config import pipeline
from lib.extract import check_status, download_data
from lib.mongo import (
    populate_raw_db,
    get_random_card,
    get_card_by_name,
    iter_raw_cards,
    count_raw_cards,
)
from lib.pipeline import start_docker_containers
from lib.transform import transform_card
from lib.postgres import (
    get_connection,
    load_transformed_card,
    load_transformed_cards,
    truncate_sql_tables,
)
from lib.load import save_price_dataframe
from lib.ml_pipeline import build_model, predict_card_price

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

    import_parser = subparsers.add_parser(
        "importsql",
        help="Batch import all raw MongoDB cards into Postgres",
    )
    import_parser.add_argument(
        "--batch-size",
        type=int,
        default=pipeline.batch_size,
        help="Number of cards to transform and load per SQL batch",
    )
    import_parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit for testing. Use 0 for no limit.",
    )
    import_parser.add_argument(
        "--truncate",
        action="store_true",
        help="Clear SQL tables before importing",
    )

    dataframe_parser = subparsers.add_parser(
        "exportdf",
        help="Export a machine-learning price dataframe from Postgres to Parquet",
    )
    dataframe_parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Optional output path. Defaults to data/dataframe/card_price_dataframe.parquet",
    )
    dataframe_parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional row limit for testing. Use 0 for no limit.",
    )

    ml_pipeline_parser = subparsers.add_parser(
        "build_ml_model",
        help="Builds the standard ML Model, evaluates it and saves it"
    )

    predict_parser = subparsers.add_parser(
        "predictprice",
        help="Predict a card price from manually entered features",
    )

    predict_parser.add_argument("--finish", default="nonfoil")
    predict_parser.add_argument("--language", default="en")
    predict_parser.add_argument("--set-type", default="expansion")
    predict_parser.add_argument("--rarity", default="rare")
    predict_parser.add_argument("--border-color", default="black")
    predict_parser.add_argument("--frame", default="2015")
    predict_parser.add_argument("--layout", default="normal")
    predict_parser.add_argument("--colors", default="")
    predict_parser.add_argument("--games", default="paper")
    predict_parser.add_argument("--power", default="")
    predict_parser.add_argument("--toughness", default="")
    predict_parser.add_argument("--loyalty", default="")
    predict_parser.add_argument("--edhrec-rank", type=int, default=None)
    predict_parser.add_argument("--penny-rank", type=int, default=None)

    predict_parser.add_argument("--reserved", action="store_true")
    predict_parser.add_argument("--booster", action="store_true")
    predict_parser.add_argument("--digital", action="store_true")
    predict_parser.add_argument("--reprint", action="store_true")
    predict_parser.add_argument("--full-art", action="store_true")
    predict_parser.add_argument("--textless", action="store_true")

    predict_parser.add_argument("--modern-legal", default="not_legal")
    predict_parser.add_argument("--commander-legal", default="not_legal")
    predict_parser.add_argument("--legacy-legal", default="not_legal")


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

        case "importsql":
            if args.batch_size <= 0:
                raise ValueError("--batch-size must be greater than 0")

            limit = args.limit if args.limit > 0 else None
            total = count_raw_cards(limit=limit)

            print(f"Preparing SQL import for {total} cards...")
            print(f"Batch size: {args.batch_size}")

            conn = get_connection()

            try:
                if args.truncate:
                    print("Truncating SQL tables before import...")
                    truncate_sql_tables(conn) # Reset before fresh import

                imported = 0
                batch = []
                # Batch-logic. Loads batch sized amount of cards from mongodb to memory, then to SQL and clears the batch
                for raw_card in iter_raw_cards(
                    batch_size=args.batch_size,
                    limit=limit,
                ):
                    try:
                        batch.append(transform_card(raw_card))
                    except Exception as exc:
                        raise RuntimeError(
                            f"Failed to transform card "
                            f"{raw_card.get('name')} ({raw_card.get('id')})"
                        ) from exc

                    if len(batch) >= args.batch_size:
                        imported += load_transformed_cards(conn, batch)
                        print(f"Imported {imported}/{total} cards")
                        batch.clear()

                if batch:
                    imported += load_transformed_cards(conn, batch)
                    print(f"Imported {imported}/{total} cards")

                print("SQL import complete.")

            finally:
                conn.close()

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
        
        case "exportdf":
            limit = args.limit if args.limit > 0 else None
            output_path = args.output if args.output else None

            path, row_count = save_price_dataframe(
                output_path=output_path,
            )

            print(f"Saved dataframe with {row_count} rows to: {path}")

        case "build_ml_model":
            build_model()


        case "predictprice":
            colors = [color for color in args.colors.split(",") if color]
            games = [game for game in args.games.split(",") if game]

            card_features = {
                "finish": args.finish,
                "language": args.language,
                "set_type": args.set_type,
                "rarity": args.rarity,
                "border_color": args.border_color,
                "frame": args.frame,
                "layout": args.layout,
                "colors": colors,
                "games": games,
                "power": args.power or None,
                "toughness": args.toughness or None,
                "loyalty": args.loyalty or None,
                "edhrec_rank": args.edhrec_rank,
                "penny_rank": args.penny_rank,
                "reserved": args.reserved,
                "booster": args.booster,
                "digital": args.digital,
                "reprint": args.reprint,
                "full_art": args.full_art,
                "textless": args.textless,
                "modern_legal": args.modern_legal,
                "commander_legal": args.commander_legal,
                "legacy_legal": args.legacy_legal,
            }

            predicted_price = predict_card_price(card_features)

            print(f"Predicted price: {predicted_price:.2f} EUR")

        case _:
            parser.print_help()

if __name__ == "__main__":
    main()