# load.py
# Utility functions to Load and prepare data for Machine Learning from SQL BDV
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import paths
from .postgres import get_connection


DEFAULT_DATAFRAME_PATH = paths.data_dir / "dataframe" / "card_price_dataframe.parquet"


PRICE_DATAFRAME_SQL = """
WITH colors AS (
    SELECT
        card_id,
        array_to_string(array_agg(DISTINCT color ORDER BY color), '|') AS colors,
        COUNT(DISTINCT color)::INTEGER AS color_count,
        BOOL_OR(color = 'W') AS has_white,
        BOOL_OR(color = 'U') AS has_blue,
        BOOL_OR(color = 'B') AS has_black,
        BOOL_OR(color = 'R') AS has_red,
        BOOL_OR(color = 'G') AS has_green
    FROM bridge_card_colors
    GROUP BY card_id
),

keywords AS (
    SELECT
        card_id,
        array_to_string(array_agg(DISTINCT keyword ORDER BY keyword), '|') AS keywords,
        COUNT(DISTINCT keyword)::INTEGER AS keyword_count
    FROM bridge_card_keywords
    GROUP BY card_id
),

games AS (
    SELECT
        card_id,
        array_to_string(array_agg(DISTINCT game ORDER BY game), '|') AS games,
        COUNT(DISTINCT game)::INTEGER AS game_count,
        BOOL_OR(game = 'paper') AS has_game_paper,
        BOOL_OR(game = 'arena') AS has_game_arena,
        BOOL_OR(game = 'mtgo') AS has_game_mtgo
    FROM bridge_card_games
    GROUP BY card_id
),

artists AS (
    SELECT
        card_id,
        array_to_string(array_agg(DISTINCT artist ORDER BY artist), '|') AS artists,
        COUNT(DISTINCT artist)::INTEGER AS artist_count
    FROM bridge_card_artists
    GROUP BY card_id
),

legalities AS (
    SELECT
        card_id,
        jsonb_object_agg(format_name, legality ORDER BY format_name)::TEXT AS legalities_json,

        COUNT(*) FILTER (WHERE legality = 'legal')::INTEGER AS legal_format_count,
        COUNT(*) FILTER (WHERE legality = 'not_legal')::INTEGER AS not_legal_format_count,
        COUNT(*) FILTER (WHERE legality = 'banned')::INTEGER AS banned_format_count,
        COUNT(*) FILTER (WHERE legality = 'restricted')::INTEGER AS restricted_format_count,

        MAX(CASE WHEN format_name = 'standard' THEN legality END) AS legality_standard,
        MAX(CASE WHEN format_name = 'pioneer' THEN legality END) AS legality_pioneer,
        MAX(CASE WHEN format_name = 'modern' THEN legality END) AS legality_modern,
        MAX(CASE WHEN format_name = 'legacy' THEN legality END) AS legality_legacy,
        MAX(CASE WHEN format_name = 'vintage' THEN legality END) AS legality_vintage,
        MAX(CASE WHEN format_name = 'commander' THEN legality END) AS legality_commander,
        MAX(CASE WHEN format_name = 'pauper' THEN legality END) AS legality_pauper,
        MAX(CASE WHEN format_name = 'brawl' THEN legality END) AS legality_brawl,
        MAX(CASE WHEN format_name = 'historic' THEN legality END) AS legality_historic
    FROM bridge_card_legalities
    GROUP BY card_id
),

faces AS (
    SELECT
        card_id,
        COUNT(*)::INTEGER AS face_count,
        jsonb_agg(
            jsonb_build_object(
                'face_index', face_index,
                'face_name', face_name,
                'face_mana_cost', face_mana_cost,
                'face_type_line', face_type_line,
                'face_oracle_text', face_oracle_text,
                'face_power', face_power,
                'face_toughness', face_toughness,
                'face_loyalty', face_loyalty
            )
            ORDER BY face_index
        )::TEXT AS card_faces_json
    FROM card_faces
    GROUP BY card_id
)

SELECT
    fc.card_id,
    bp.finish,
    bp.price_eur::DOUBLE PRECISION AS target_price_eur,

    fc.card_name,
    fc.reserved,
    fc.booster,
    fc.digital,
    fc.reprint,
    fc.edhrec_rank,
    fc.penny_rank,
    fc.full_art,
    fc.textless,

    dtl.type_line,
    dmc.mana_cost,
    drd.release_date,
    dlang.language,
    dotx.oracle_text,
    dpow.power,
    dtough.toughness,
    dloy.loyalty,
    dset.set_code,
    dset.set_name,
    dset.set_type,
    drar.rarity,
    dbc.border_color,
    dframe.frame,
    dlay.layout,

    COALESCE(colors.colors, '') AS colors,
    COALESCE(colors.color_count, 0) AS color_count,
    COALESCE(colors.has_white, FALSE) AS has_white,
    COALESCE(colors.has_blue, FALSE) AS has_blue,
    COALESCE(colors.has_black, FALSE) AS has_black,
    COALESCE(colors.has_red, FALSE) AS has_red,
    COALESCE(colors.has_green, FALSE) AS has_green,

    COALESCE(keywords.keywords, '') AS keywords,
    COALESCE(keywords.keyword_count, 0) AS keyword_count,

    COALESCE(games.games, '') AS games,
    COALESCE(games.game_count, 0) AS game_count,
    COALESCE(games.has_game_paper, FALSE) AS has_game_paper,
    COALESCE(games.has_game_arena, FALSE) AS has_game_arena,
    COALESCE(games.has_game_mtgo, FALSE) AS has_game_mtgo,

    COALESCE(artists.artists, '') AS artists,
    COALESCE(artists.artist_count, 0) AS artist_count,

    COALESCE(legalities.legalities_json, '{}') AS legalities_json,
    COALESCE(legalities.legal_format_count, 0) AS legal_format_count,
    COALESCE(legalities.not_legal_format_count, 0) AS not_legal_format_count,
    COALESCE(legalities.banned_format_count, 0) AS banned_format_count,
    COALESCE(legalities.restricted_format_count, 0) AS restricted_format_count,

    COALESCE(legalities.legality_standard, 'unknown') AS legality_standard,
    COALESCE(legalities.legality_pioneer, 'unknown') AS legality_pioneer,
    COALESCE(legalities.legality_modern, 'unknown') AS legality_modern,
    COALESCE(legalities.legality_legacy, 'unknown') AS legality_legacy,
    COALESCE(legalities.legality_vintage, 'unknown') AS legality_vintage,
    COALESCE(legalities.legality_commander, 'unknown') AS legality_commander,
    COALESCE(legalities.legality_pauper, 'unknown') AS legality_pauper,
    COALESCE(legalities.legality_brawl, 'unknown') AS legality_brawl,
    COALESCE(legalities.legality_historic, 'unknown') AS legality_historic,

    COALESCE(faces.face_count, 0) AS face_count,
    COALESCE(faces.card_faces_json, '[]') AS card_faces_json

FROM bridge_card_prices AS bp

JOIN fact_cards AS fc
    ON fc.card_id = bp.card_id

LEFT JOIN dim_type_line AS dtl
    ON dtl.id = fc.type_line_id

LEFT JOIN dim_mana_cost AS dmc
    ON dmc.id = fc.mana_cost_id

LEFT JOIN dim_release_date AS drd
    ON drd.id = fc.release_date_id

LEFT JOIN dim_language AS dlang
    ON dlang.id = fc.language_id

LEFT JOIN dim_oracle_text AS dotx
    ON dotx.id = fc.oracle_text_id

LEFT JOIN dim_power AS dpow
    ON dpow.id = fc.power_id

LEFT JOIN dim_toughness AS dtough
    ON dtough.id = fc.toughness_id

LEFT JOIN dim_loyalty AS dloy
    ON dloy.id = fc.loyalty_id

LEFT JOIN dim_set AS dset
    ON dset.id = fc.set_id

LEFT JOIN dim_rarity AS drar
    ON drar.id = fc.rarity_id

LEFT JOIN dim_border_color AS dbc
    ON dbc.id = fc.border_color_id

LEFT JOIN dim_frame AS dframe
    ON dframe.id = fc.frame_id

LEFT JOIN dim_layout AS dlay
    ON dlay.id = fc.layout_id

LEFT JOIN colors
    ON colors.card_id = fc.card_id

LEFT JOIN keywords
    ON keywords.card_id = fc.card_id

LEFT JOIN games
    ON games.card_id = fc.card_id

LEFT JOIN artists
    ON artists.card_id = fc.card_id

LEFT JOIN legalities
    ON legalities.card_id = fc.card_id

LEFT JOIN faces
    ON faces.card_id = fc.card_id

WHERE bp.price_eur IS NOT NULL

ORDER BY fc.card_id, bp.finish
"""


def _postprocess_price_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply light dataframe cleanup after loading from SQL.

    This does not do full ML feature engineering yet.
    It only makes the exported dataframe cleaner and easier to use later.
    """
    if df.empty:
        return df

    df = df.copy()

    df["target_price_eur"] = pd.to_numeric(
        df["target_price_eur"],
        errors="coerce",
    )

    df = df.dropna(subset=["target_price_eur"]).copy()

    if "release_date" in df.columns:
        df["release_date"] = pd.to_datetime(
            df["release_date"],
            errors="coerce",
        )

        df["release_year"] = df["release_date"].dt.year.astype("Int64")
        df["release_month"] = df["release_date"].dt.month.astype("Int64")

    bool_columns = [
        "reserved",
        "booster",
        "digital",
        "reprint",
        "full_art",
        "textless",
        "has_white",
        "has_blue",
        "has_black",
        "has_red",
        "has_green",
        "has_game_paper",
        "has_game_arena",
        "has_game_mtgo",
    ]

    for column in bool_columns:
        if column in df.columns:
            df[column] = df[column].fillna(False).astype(bool)

    count_columns = [
        "color_count",
        "keyword_count",
        "game_count",
        "artist_count",
        "legal_format_count",
        "not_legal_format_count",
        "banned_format_count",
        "restricted_format_count",
        "face_count",
    ]

    for column in count_columns:
        if column in df.columns:
            df[column] = df[column].fillna(0).astype("Int64")

    text_columns = [
        "finish",
        "card_name",
        "type_line",
        "mana_cost",
        "language",
        "oracle_text",
        "power",
        "toughness",
        "loyalty",
        "set_code",
        "set_name",
        "set_type",
        "rarity",
        "border_color",
        "frame",
        "layout",
        "colors",
        "keywords",
        "games",
        "artists",
        "legalities_json",
        "legality_standard",
        "legality_pioneer",
        "legality_modern",
        "legality_legacy",
        "legality_vintage",
        "legality_commander",
        "legality_pauper",
        "legality_brawl",
        "legality_historic",
        "card_faces_json",
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = df[column].fillna("")

    return df


def load_price_dataframe(limit: int | None = None) -> pd.DataFrame:
    """
    Load a machine-learning-oriented price dataframe from Postgres.

    Row grain:
        one row per card_id + finish price

    Target column:
        target_price_eur
    """
    sql_query = PRICE_DATAFRAME_SQL
    params = None

    if limit is not None:
        sql_query = f"{sql_query}\nLIMIT %(limit)s"
        params = {"limit": limit}

    conn = get_connection()

    try:
        df = pd.read_sql_query(
            sql_query,
            conn,
            params=params,
        )
    finally:
        conn.close()

    return _postprocess_price_dataframe(df)


def save_price_dataframe(
    output_path: str | Path | None = None,
    limit: int | None = None,
) -> tuple[Path, int]:
    """
    Load the ML price dataframe from Postgres and save it as a Parquet file.
    """
    if output_path is None:
        output_path = DEFAULT_DATAFRAME_PATH

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_price_dataframe(limit=limit)

    if df.empty:
        raise ValueError("The price dataframe is empty. Check whether SQL price data exists.")

    df.to_parquet(
        output_path,
        index=False,
        engine="pyarrow",
    )

    return output_path, len(df)