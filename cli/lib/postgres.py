# postgress.py
# Utility Functions to insert, upsert and query the SQL Data
from typing import Any
from collections.abc import Sequence # allows further flexibility going forward

import psycopg2
from psycopg2 import sql # allows to dynamically use column and table names
from psycopg2.extras import execute_values # used to insert many rows in one operation

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
    
    card_face_rows = [
        (
            card_id,
            face["face_index"],
            face["face_name"],
            face["face_mana_cost"],
            face["face_type_line"],
            face["face_oracle_text"],
            face["face_power"],
            face["face_toughness"],
            face["face_loyalty"],
        )
        for face in bridges["card_faces"]
    ]

    if card_face_rows:
        execute_values(
            cur,
            """
            INSERT INTO card_faces (
                card_id,
                face_index,
                face_name,
                face_mana_cost,
                face_type_line,
                face_oracle_text,
                face_power,
                face_toughness,
                face_loyalty
            )
            VALUES %s
            ON CONFLICT (card_id, face_index)
            DO UPDATE SET
                face_name = EXCLUDED.face_name,
                face_mana_cost = EXCLUDED.face_mana_cost,
                face_type_line = EXCLUDED.face_type_line,
                face_oracle_text = EXCLUDED.face_oracle_text,
                face_power = EXCLUDED.face_power,
                face_toughness = EXCLUDED.face_toughness,
                face_loyalty = EXCLUDED.face_loyalty;
            """,
            card_face_rows,
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

# mapping to loop over for each dimension and bridge
SINGLE_COLUMN_DIMENSIONS = {
    "type_line": ("dim_type_line", "type_line"),
    "mana_cost": ("dim_mana_cost", "mana_cost"),
    "release_date": ("dim_release_date", "release_date"),
    "language": ("dim_language", "language"),
    "oracle_text": ("dim_oracle_text", "oracle_text"),
    "power": ("dim_power", "power"),
    "toughness": ("dim_toughness", "toughness"),
    "loyalty": ("dim_loyalty", "loyalty"),
    "rarity": ("dim_rarity", "rarity"),
    "border_color": ("dim_border_color", "border_color"),
    "frame": ("dim_frame", "frame"),
    "layout": ("dim_layout", "layout"),
}
# used to refresh bridge rows
BRIDGE_TABLES = [
    "bridge_card_colors",
    "bridge_card_keywords",
    "bridge_card_games",
    "bridge_card_artists",
    "bridge_card_legalities",
    "bridge_card_prices",
    "card_faces",
]


def _key(value: Any) -> str | None:
    # This converts a value into a string key for dictionary lookup.
    if value is None:
        return None
    return str(value)


def _unique_non_null(values: list[Any]) -> list[Any]:
    # removes duplicate values from a list (dimension values cleanup)
    seen = set()
    result = []

    for value in values:
        if value is None:
            continue

        key = str(value)

        if key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result


def _dedupe_rows(rows: list[tuple]) -> list[tuple]:
    # removes duplicate row tuples while preserving order (bridge table cleanup)
    return list(dict.fromkeys(rows))


def _upsert_single_dimension_values(
    cur,
    table_name: str,
    column_name: str,
    values: list[Any],
) -> dict[str, int]:
    """
    For one dimension table:
    1. collect all unique non-null values
    2. insert missing values
    3. fetch IDs for all values (old IDs for existing values)
    4. return a mapping from value to ID -> for foreign Keys
    """
    unique_values = _unique_non_null(values)

    if not unique_values:
        return {}

    insert_query = sql.SQL(
        """
        INSERT INTO {table} ({column})
        VALUES %s
        ON CONFLICT ({column}) DO NOTHING;
        """
    ).format(
        table=sql.Identifier(table_name),
        column=sql.Identifier(column_name),
    )

    execute_values(
        cur,
        insert_query.as_string(cur),
        [(value,) for value in unique_values],
        page_size=1000,
    )

    select_query = sql.SQL(
        """
        SELECT {column}::text, id
        FROM {table}
        WHERE {column} IN %s;
        """
    ).format(
        table=sql.Identifier(table_name),
        column=sql.Identifier(column_name),
    )

    cur.execute(select_query, (tuple(unique_values),))

    return {str(value): id_ for value, id_ in cur.fetchall()}


def _upsert_set_values(cur, transformed_cards: Sequence[dict[str, Any]]) -> dict[str, int]:
    """
    Specific function for the set dimension, as it has multiple values to insert
    1. collect all sets from the batch
    2. deduplicate by set_code
    3. insert or update dim_set
    4. fetch IDs by set_code
    5. return {set_code: id}
    """
    rows_by_set_code: dict[str, tuple[str, str | None, str | None]] = {}

    for transformed_card in transformed_cards:
        set_dim = transformed_card["dimensions"]["set"]
        set_code = set_dim["set"]

        if set_code is None:
            continue

        rows_by_set_code[str(set_code)] = (
            set_code,
            set_dim["set_name"],
            set_dim["set_type"],
        )

    if not rows_by_set_code:
        return {}

    rows = list(rows_by_set_code.values())

    execute_values(
        cur,
        """
        INSERT INTO dim_set (set_code, set_name, set_type)
        VALUES %s
        ON CONFLICT (set_code)
        DO UPDATE SET
            set_name = EXCLUDED.set_name,
            set_type = EXCLUDED.set_type;
        """,
        rows,
        page_size=1000,
    )

    cur.execute(
        """
        SELECT set_code, id
        FROM dim_set
        WHERE set_code IN %s;
        """,
        (tuple(rows_by_set_code.keys()),),
    )

    return {str(set_code): id_ for set_code, id_ in cur.fetchall()}


def _lookup_dimension_id(mapping: dict[str, int], value: Any) -> int | None:
    # Helper to convert raw dimension values into IDs
    key = _key(value)

    if key is None:
        return None

    return mapping.get(key)


def _delete_existing_bridge_rows(cur, card_ids: list[str]) -> None:
    """
    Delete bridge rows for cards in this batch.

    This makes re-imports safer because removed colors, keywords, prices,
    legalities, etc. do not remain as stale bridge rows.
    """
    unique_card_ids = list(dict.fromkeys(card_ids))

    if not unique_card_ids:
        return

    for table_name in BRIDGE_TABLES:
        query = sql.SQL(
            """
            DELETE FROM {table}
            WHERE card_id IN %s;
            """
        ).format(table=sql.Identifier(table_name))

        cur.execute(query, (tuple(unique_card_ids),))


def _build_fact_rows(
    transformed_cards: Sequence[dict[str, Any]], # most likely a list, but Sequence is more flexible for future implementations
    dimension_maps: dict[str, dict[str, int]],
    set_map: dict[str, int],
) -> list[tuple]:
    '''
    Takes the transformed cards and builds the necessary rows for the fact table including all foreign IDs (through the helper function)
    '''
    fact_rows = []

    for transformed_card in transformed_cards:
        card = transformed_card["card"]
        dimensions = transformed_card["dimensions"]

        card_id = card["card_id"]

        if card_id is None:
            continue

        fact_rows.append(
            (
                card_id,
                card["card_name"],
                card["reserved"],
                card["booster"],
                card["digital"],
                card["reprint"],
                card["edhrec_rank"],
                card["penny_rank"],
                card["full_art"],
                card["textless"],
                _lookup_dimension_id(
                    dimension_maps["type_line"],
                    dimensions["type_line"]["type_line"],
                ),
                _lookup_dimension_id(
                    dimension_maps["mana_cost"],
                    dimensions["mana_cost"]["mana_cost"],
                ),
                _lookup_dimension_id(
                    dimension_maps["release_date"],
                    dimensions["release_date"]["release_date"],
                ),
                _lookup_dimension_id(
                    dimension_maps["language"],
                    dimensions["language"]["language"],
                ),
                _lookup_dimension_id(
                    dimension_maps["oracle_text"],
                    dimensions["oracle_text"]["oracle_text"],
                ),
                _lookup_dimension_id(
                    dimension_maps["power"],
                    dimensions["power"]["power"],
                ),
                _lookup_dimension_id(
                    dimension_maps["toughness"],
                    dimensions["toughness"]["toughness"],
                ),
                _lookup_dimension_id(
                    dimension_maps["loyalty"],
                    dimensions["loyalty"]["loyalty"],
                ),
                _lookup_dimension_id(
                    set_map,
                    dimensions["set"]["set"],
                ),
                _lookup_dimension_id(
                    dimension_maps["rarity"],
                    dimensions["rarity"]["rarity"],
                ),
                _lookup_dimension_id(
                    dimension_maps["border_color"],
                    dimensions["border_color"]["border_color"],
                ),
                _lookup_dimension_id(
                    dimension_maps["frame"],
                    dimensions["frame"]["frame"],
                ),
                _lookup_dimension_id(
                    dimension_maps["layout"],
                    dimensions["layout"]["layout"],
                ),
            )
        )

    return fact_rows


def _insert_fact_rows(cur, fact_rows: list[tuple]) -> None:
    '''
    Inserts the rows built above in SQL
    '''
    if not fact_rows:
        return

    execute_values(
        cur,
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
        VALUES %s
        ON CONFLICT (card_id)
        DO UPDATE SET
            card_name = EXCLUDED.card_name,
            reserved = EXCLUDED.reserved,
            booster = EXCLUDED.booster,
            digital = EXCLUDED.digital,
            reprint = EXCLUDED.reprint,
            edhrec_rank = EXCLUDED.edhrec_rank,
            penny_rank = EXCLUDED.penny_rank,
            full_art = EXCLUDED.full_art,
            textless = EXCLUDED.textless,
            type_line_id = EXCLUDED.type_line_id,
            mana_cost_id = EXCLUDED.mana_cost_id,
            release_date_id = EXCLUDED.release_date_id,
            language_id = EXCLUDED.language_id,
            oracle_text_id = EXCLUDED.oracle_text_id,
            power_id = EXCLUDED.power_id,
            toughness_id = EXCLUDED.toughness_id,
            loyalty_id = EXCLUDED.loyalty_id,
            set_id = EXCLUDED.set_id,
            rarity_id = EXCLUDED.rarity_id,
            border_color_id = EXCLUDED.border_color_id,
            frame_id = EXCLUDED.frame_id,
            layout_id = EXCLUDED.layout_id;
        """,
        fact_rows,
        page_size=1000,
    )


def _collect_bridge_rows(
    transformed_cards: Sequence[dict[str, Any]],
) -> dict[str, list[tuple]]:
    '''
    Collects bridge rows and returns them, extend appends multiple values from the iterable provided
    '''
    rows = {
        "colors": [],
        "keywords": [],
        "games": [],
        "artists": [],
        "legalities": [],
        "prices": [],
        "card_faces": [],
    }

    for transformed_card in transformed_cards:
        card_id = transformed_card["card"]["card_id"]

        if card_id is None:
            continue

        bridges = transformed_card["bridges"]

        rows["colors"].extend(
            (card_id, color)
            for color in bridges["colors"]
            if color is not None
        )

        rows["keywords"].extend(
            (card_id, keyword)
            for keyword in bridges["keywords"]
            if keyword is not None
        )

        rows["games"].extend(
            (card_id, game)
            for game in bridges["games"]
            if game is not None
        )

        rows["artists"].extend(
            (card_id, artist)
            for artist in bridges["artists"]
            if artist is not None
        )

        rows["legalities"].extend(
            (card_id, item["format"], item["legality"])
            for item in bridges["legalities"]
            if item.get("format") is not None and item.get("legality") is not None
        )

        rows["prices"].extend(
            (card_id, item["finish"], item["price_eur"])
            for item in bridges["price_rows"]
            if item.get("finish") is not None and item.get("price_eur") is not None
        )

        rows["card_faces"].extend(
            (
                card_id,
                face["face_index"],
                face["face_name"],
                face["face_mana_cost"],
                face["face_type_line"],
                face["face_oracle_text"],
                face["face_power"],
                face["face_toughness"],
                face["face_loyalty"],
            )
            for face in bridges["card_faces"]
        )

    return rows


def _insert_bridge_rows_batch(cur, bridge_rows: dict[str, list[tuple]]) -> None:
    '''
    Inserts the bridge rows created to SQL after removing duplicates.
    '''
    color_rows = _dedupe_rows(bridge_rows["colors"])

    if color_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_colors (card_id, color)
            VALUES %s
            ON CONFLICT DO NOTHING;
            """,
            color_rows,
            page_size=1000,
        )

    keyword_rows = _dedupe_rows(bridge_rows["keywords"])

    if keyword_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_keywords (card_id, keyword)
            VALUES %s
            ON CONFLICT DO NOTHING;
            """,
            keyword_rows,
            page_size=1000,
        )

    game_rows = _dedupe_rows(bridge_rows["games"])

    if game_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_games (card_id, game)
            VALUES %s
            ON CONFLICT DO NOTHING;
            """,
            game_rows,
            page_size=1000,
        )

    artist_rows = _dedupe_rows(bridge_rows["artists"])

    if artist_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_artists (card_id, artist)
            VALUES %s
            ON CONFLICT DO NOTHING;
            """,
            artist_rows,
            page_size=1000,
        )

    legality_rows = _dedupe_rows(bridge_rows["legalities"])

    if legality_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_legalities (card_id, format_name, legality)
            VALUES %s
            ON CONFLICT (card_id, format_name)
            DO UPDATE SET legality = EXCLUDED.legality;
            """,
            legality_rows,
            page_size=1000,
        )

    price_rows = _dedupe_rows(bridge_rows["prices"])

    if price_rows:
        execute_values(
            cur,
            """
            INSERT INTO bridge_card_prices (card_id, finish, price_eur)
            VALUES %s
            ON CONFLICT (card_id, finish)
            DO UPDATE SET price_eur = EXCLUDED.price_eur;
            """,
            price_rows,
            page_size=1000,
        )
    
    card_face_rows = _dedupe_rows(bridge_rows["card_faces"])

    if card_face_rows:
        execute_values(
            cur,
            """
            INSERT INTO card_faces (
                card_id,
                face_index,
                face_name,
                face_mana_cost,
                face_type_line,
                face_oracle_text,
                face_power,
                face_toughness,
                face_loyalty
            )
            VALUES %s
            ON CONFLICT (card_id, face_index)
            DO UPDATE SET
                face_name = EXCLUDED.face_name,
                face_mana_cost = EXCLUDED.face_mana_cost,
                face_type_line = EXCLUDED.face_type_line,
                face_oracle_text = EXCLUDED.face_oracle_text,
                face_power = EXCLUDED.face_power,
                face_toughness = EXCLUDED.face_toughness,
                face_loyalty = EXCLUDED.face_loyalty;
            """,
            card_face_rows,
            page_size=1000,
        )


def load_transformed_cards(
    conn,
    transformed_cards: Sequence[dict[str, Any]],
) -> int:
    """
    Load a batch of transformed cards into Postgres.

    One batch = one transaction.

    This function:
    - upserts dimension values in bulk
    - upserts fact_cards in bulk
    - deletes old bridge rows for cards in this batch
    - inserts current bridge rows in bulk
    - returns the amount of cards it loaded
    """
    # Create a dictionary, mapping the card id to the transformed cards
    cards_by_id: dict[str, dict[str, Any]] = {}

    for transformed_card in transformed_cards:
        card_id = transformed_card["card"]["card_id"]

        if card_id is not None:
            cards_by_id[str(card_id)] = transformed_card

    cards = list(cards_by_id.values())

    if not cards:
        return 0

    # Start of the transaction (order is important!! dimension before fact before bridge)
    try:
        with conn.cursor() as cur:
            dimension_maps: dict[str, dict[str, int]] = {}
            # iterate over the dimensions from the mapping then use upsert helpers to upsert in SQL
            for dimension_name, (
                table_name,
                column_name,
            ) in SINGLE_COLUMN_DIMENSIONS.items():
                values = [
                    transformed_card["dimensions"][dimension_name][column_name]
                    for transformed_card in cards
                ]

                dimension_maps[dimension_name] = _upsert_single_dimension_values(
                    cur,
                    table_name,
                    column_name,
                    values,
                )
            # use set helper to upsert in SQL
            set_map = _upsert_set_values(cur, cards)

            # get list of card ids
            card_ids = [
                transformed_card["card"]["card_id"]
                for transformed_card in cards
                if transformed_card["card"]["card_id"] is not None
            ]

            # delete the existing bridges to freshly insert
            _delete_existing_bridge_rows(cur, card_ids)

            # use fact row builder helper
            fact_rows = _build_fact_rows(
                cards,
                dimension_maps,
                set_map,
            )
            # insert the fact row
            _insert_fact_rows(cur, fact_rows)

            # insert bridges and assign FKs accordingly
            bridge_rows = _collect_bridge_rows(cards)
            _insert_bridge_rows_batch(cur, bridge_rows)

        conn.commit()
        return len(cards)

    except Exception:
        conn.rollback() # fall back in case something goes wrong, the database is reset to the state before the batch
        raise


def truncate_sql_tables(conn) -> None:
    """
    Full-refresh helper.

    Clears fact, bridge, and dimension tables before a fresh import.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                TRUNCATE TABLE
                    bridge_card_prices,
                    bridge_card_legalities,
                    bridge_card_artists,
                    bridge_card_games,
                    bridge_card_keywords,
                    bridge_card_colors,
                    card_faces,
                    fact_cards,
                    dim_type_line,
                    dim_mana_cost,
                    dim_release_date,
                    dim_language,
                    dim_oracle_text,
                    dim_power,
                    dim_toughness,
                    dim_loyalty,
                    dim_set,
                    dim_rarity,
                    dim_border_color,
                    dim_frame,
                    dim_layout
                RESTART IDENTITY CASCADE;
                """
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise