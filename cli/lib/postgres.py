# Utility Functions to insert, upsert and query the SQL Data
import psycopg2
from psycopg2.extras import execute_values
from .config import postgres

def get_connection():
    return psycopg2.connect(
        host=postgres.host,
        port=postgres.port,
        user=postgres.username,
        password=postgres.password,
        dbname=postgres.database,
    )


def get_or_create_dimension(cur, table_name: str, column_name: str, value):
    '''Insert this dimension value if it doesn't exist yet, otherwise reuse the existing one and always give me its id'''
    if value is None:
        return None

    cur.execute(
        f"""
        INSERT INTO {table_name} ({column_name})
        VALUES (%s)
        ON CONFLICT ({column_name})
        DO UPDATE SET {column_name} = EXCLUDED.{column_name}
        RETURNING id;
        """,
        (value,),
    )

    return cur.fetchone()[0]

def get_or_create_multicol_dimension(cur, set_code: str | None, set_name: str | None, set_type: str | None):
    '''Same as the function above, but for dimensions with more than one column'''
    if set_code is None:
        return None

    cur.execute(
        """
        INSERT INTO dim_set (set_code, set_name, set_type)
        VALUES (%s, %s, %s)
        ON CONFLICT (set_code)
        DO UPDATE SET
            set_name = EXCLUDED.set_name,
            set_type = EXCLUDED.set_type
        RETURNING id;
        """,
        (set_code, set_name, set_type),
    )

    return cur.fetchone()[0]

def insert_bridge_rows(cur, card_id: str, bridges: dict) -> None:
    '''Inserts all related multi-value attributes into bridge tables for one cardID'''
    color_rows = [(card_id, color) for color in bridges["colors"]]
    # Convert list values into row tuples for bulk insertion. ["value1", "value2"] to ("cardID", "value1") and ("cardID", "value2")
    if color_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_colors (card_id, color)
            VALUES %s
            ON CONFLICT DO NOTHING;
            """,
            color_rows,
        )

    keyword_rows = [(card_id, keyword) for keyword in bridges["keywords"]]

    if keyword_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_keywords (card_id, keyword)
            VALUES %s
            ON CONFLICT DO NOTHING;
            """,
            keyword_rows,
        )

    game_rows = [(card_id, game) for game in bridges["games"]]

    if game_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_games (card_id, game)
            VALUES %s
            ON CONFLICT DO NOTHING;
            """,
            game_rows,
        )

    artist_rows = [(card_id, artist) for artist in bridges["artists"]]

    if artist_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_artists (card_id, artist)
            VALUES %s
            ON CONFLICT DO NOTHING;
            """,
            artist_rows,
        )

    legality_rows = [
        (card_id, item["format"], item["legality"])
        for item in bridges["legalities"]
    ]

    if legality_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_legalities (card_id, format_name, legality)
            VALUES %s
            ON CONFLICT DO NOTHING;
            """,
            legality_rows,
        )

    price_rows = [
        (card_id, item["finish"], item["price_eur"])
        for item in bridges["price_rows"]
    ]

    if price_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_prices (card_id, finish, price_eur)
            VALUES %s
            ON CONFLICT DO NOTHING;
            """,
            price_rows,
        )

def load_transformed_card(conn, transformed_card: dict) -> None:
    '''Load a single card to all relevant SQL tables'''
    try:
        card = transformed_card["card"]
        dimensions = transformed_card["dimensions"]
        bridges = transformed_card["bridges"]

        with conn.cursor() as cur:
            type_line_id = get_or_create_dimension(
                cur,
                "dim_type_line",
                "type_line",
                dimensions["type_line"]["type_line"],
            )

            mana_cost_id = get_or_create_dimension(
                cur,
                "dim_mana_cost",
                "mana_cost",
                dimensions["mana_cost"]["mana_cost"],
            )

            release_date_id = get_or_create_dimension(
                cur,
                "dim_release_date",
                "release_date",
                dimensions["release_date"]["release_date"]
            )

            language_id = get_or_create_dimension(
                cur,
                "dim_language",
                "language",
                dimensions["language"]["language"]
            )

            oracle_text_id = get_or_create_dimension(
                cur,
                "dim_oracle_text",
                "oracle_text",
                dimensions["oracle_text"]["oracle_text"]
            )

            power_id = get_or_create_dimension(
                cur,
                "dim_power",
                "power",
                dimensions["power"]["power"]
            )


            toughness_id = get_or_create_dimension(
                cur,
                "dim_toughness",
                "toughness",
                dimensions["toughness"]["toughness"]
            )

            loyalty_id = get_or_create_dimension(
                cur,
                "dim_loyalty",
                "loyalty",
                dimensions["loyalty"]["loyalty"]
            )

            set_id = get_or_create_multicol_dimension(
                cur,
                dimensions["set"]["set"],
                dimensions["set"]["set_name"],
                dimensions["set"]["set_type"],
            )

            rarity_id = get_or_create_dimension(
                cur,
                "dim_rarity",
                "rarity",
                dimensions["rarity"]["rarity"],
            )

            border_color_id = get_or_create_dimension(
                cur,
                "dim_border_color",
                "border_color",
                dimensions["border_color"]["border_color"],
            )

            frame_id = get_or_create_dimension(
                cur,
                "dim_frame",
                "frame",
                dimensions["frame"]["frame"],
            )

            layout_id = get_or_create_dimension(
                cur,
                "dim_layout",
                "layout",
                dimensions["layout"]["layout"],
            )

            cur.execute(
                """
                INSERT INTO fact_cards (
                    card_id,
                    card_name,
                    reserved,
                    booster,
                    digital,
                    reprint,
                    edhrec_rank,
                    penny_rank,
                    full_art,
                    textless,
                    type_line_id,
                    mana_cost_id,
                    release_date_id,
                    language_id,
                    oracle_text_id,
                    power_id,
                    toughness_id,
                    loyalty_id,
                    set_id,
                    rarity_id,
                    border_color_id,
                    frame_id,
                    layout_id
                )
                VALUES (
                    %(card_id)s,
                    %(card_name)s,
                    %(reserved)s,
                    %(booster)s,
                    %(digital)s,
                    %(reprint)s,
                    %(edhrec_rank)s,
                    %(penny_rank)s,
                    %(full_art)s,
                    %(textless)s,
                    %(type_line_id)s,
                    %(mana_cost_id)s,
                    %(release_date_id)s,
                    %(language_id)s,
                    %(oracle_text_id)s,
                    %(power_id)s,
                    %(toughness_id)s,
                    %(loyalty_id)s,
                    %(set_id)s,
                    %(rarity_id)s,
                    %(border_color_id)s,
                    %(frame_id)s,
                    %(layout_id)s
                )
                ON CONFLICT (card_id)
                DO NOTHING;
                """,
                {
                    **card,
                    "type_line_id": type_line_id,
                    "mana_cost_id": mana_cost_id,
                    "release_date_id": release_date_id,
                    "language_id": language_id,
                    "oracle_text_id": oracle_text_id,
                    "power_id": power_id,
                    "toughness_id": toughness_id,
                    "loyalty_id": loyalty_id,
                    "set_id": set_id,
                    "rarity_id": rarity_id,
                    "border_color_id": border_color_id,
                    "frame_id": frame_id,
                    "layout_id": layout_id,
                },
            )

            insert_bridge_rows(cur, card["card_id"], bridges)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

def create_tables(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
    CREATE TABLE IF NOT EXISTS dim_type_line (
        id SERIAL PRIMARY KEY,
        type_line TEXT UNIQUE
    );

    CREATE TABLE IF NOT EXISTS dim_mana_cost (
        id SERIAL PRIMARY KEY,
        mana_cost TEXT UNIQUE
    );

    CREATE TABLE IF NOT EXISTS dim_rarity (
        id SERIAL PRIMARY KEY,
        rarity TEXT UNIQUE
    );

    CREATE TABLE IF NOT EXISTS dim_layout (
        id SERIAL PRIMARY KEY,
        layout TEXT UNIQUE
    );

    CREATE TABLE IF NOT EXISTS fact_cards (
        card_id TEXT PRIMARY KEY,
        card_name TEXT,
        reserved BOOLEAN,
        booster BOOLEAN,
        digital BOOLEAN,
        reprint BOOLEAN,
        edhrec_rank INTEGER,
        penny_rank INTEGER,
        full_art BOOLEAN,
        textless BOOLEAN,
        type_line_id INTEGER REFERENCES dim_type_line(id),
        mana_cost_id INTEGER REFERENCES dim_mana_cost(id),
        rarity_id INTEGER REFERENCES dim_rarity(id),
        layout_id INTEGER REFERENCES dim_layout(id)
    );

    CREATE TABLE IF NOT EXISTS bridge_card_colors (
        card_id TEXT REFERENCES fact_cards(card_id),
        color TEXT,
        UNIQUE (card_id, color)
    );

    CREATE TABLE IF NOT EXISTS bridge_card_keywords (
        card_id TEXT REFERENCES fact_cards(card_id),
        keyword TEXT,
        UNIQUE (card_id, keyword)
    );

    CREATE TABLE IF NOT EXISTS bridge_card_games (
        card_id TEXT REFERENCES fact_cards(card_id),
        game TEXT,
        UNIQUE (card_id, game)
    );

    CREATE TABLE IF NOT EXISTS bridge_card_artists (
        card_id TEXT REFERENCES fact_cards(card_id),
        artist TEXT,
        UNIQUE (card_id, artist)
    );

    CREATE TABLE IF NOT EXISTS bridge_card_legalities (
        card_id TEXT REFERENCES fact_cards(card_id),
        format_name TEXT,
        legality TEXT,
        UNIQUE (card_id, format_name)
    );

    CREATE TABLE IF NOT EXISTS bridge_card_prices (
        card_id TEXT REFERENCES fact_cards(card_id),
        finish TEXT,
        price_eur NUMERIC,
        UNIQUE (card_id, finish)
    );
        """)
    conn.commit()