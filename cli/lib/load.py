# load.py
# Utility function to Load data for Machine Learning from SQL BDV
from pathlib import Path

import pandas as pd

from .config import paths
from .postgres import get_connection

PRICE_DATAFRAME_SQL = """
WITH colors AS (
    SELECT
        card_id,
        array_agg(DISTINCT color ORDER BY color) AS colors
    FROM bridge_card_colors
    GROUP BY card_id
),

keywords AS (
    SELECT
        card_id,
        array_agg(DISTINCT keyword ORDER BY keyword) AS keywords
    FROM bridge_card_keywords
    GROUP BY card_id
),

games AS (
    SELECT
        card_id,
        array_agg(DISTINCT game ORDER BY game) AS games
    FROM bridge_card_games
    GROUP BY card_id
),

artists AS (
    SELECT
        card_id,
        array_agg(DISTINCT artist ORDER BY artist) AS artists
    FROM bridge_card_artists
    GROUP BY card_id
),

legalities AS (
    SELECT
        card_id,

        MAX(CASE WHEN format_name = 'standard' THEN legality END) AS standard_legal,
        MAX(CASE WHEN format_name = 'future' THEN legality END) AS future_legal,
        MAX(CASE WHEN format_name = 'historic' THEN legality END) AS historic_legal,
        MAX(CASE WHEN format_name = 'timeless' THEN legality END) AS timeless_legal,
        MAX(CASE WHEN format_name = 'gladiator' THEN legality END) AS gladiator_legal,
        MAX(CASE WHEN format_name = 'pioneer' THEN legality END) AS pioneer_legal,
        MAX(CASE WHEN format_name = 'explorer' THEN legality END) AS explorer_legal,
        MAX(CASE WHEN format_name = 'modern' THEN legality END) AS modern_legal,
        MAX(CASE WHEN format_name = 'legacy' THEN legality END) AS legacy_legal,
        MAX(CASE WHEN format_name = 'pauper' THEN legality END) AS pauper_legal,
        MAX(CASE WHEN format_name = 'vintage' THEN legality END) AS vintage_legal,
        MAX(CASE WHEN format_name = 'penny' THEN legality END) AS penny_legal,
        MAX(CASE WHEN format_name = 'commander' THEN legality END) AS commander_legal,
        MAX(CASE WHEN format_name = 'oathbreaker' THEN legality END) AS oathbreaker_legal,
        MAX(CASE WHEN format_name = 'standardbrawl' THEN legality END) AS standardbrawl_legal,
        MAX(CASE WHEN format_name = 'brawl' THEN legality END) AS brawl_legal,
        MAX(CASE WHEN format_name = 'alchemy' THEN legality END) AS alchemy_legal,
        MAX(CASE WHEN format_name = 'paupercommander' THEN legality END) AS paupercommander_legal,
        MAX(CASE WHEN format_name = 'duel' THEN legality END) AS duel_legal,
        MAX(CASE WHEN format_name = 'oldschool' THEN legality END) AS oldschool_legal,
        MAX(CASE WHEN format_name = 'premodern' THEN legality END) AS premodern_legal,
        MAX(CASE WHEN format_name = 'predh' THEN legality END) AS predh_legal

    FROM bridge_card_legalities
    GROUP BY card_id
)

SELECT
    fc.card_id,
    bp.finish,
    bp.price_eur AS target_price_eur,

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

    colors.colors,
    keywords.keywords,
    games.games,
    artists.artists,

    legalities.standard_legal,
    legalities.future_legal,
    legalities.historic_legal,
    legalities.timeless_legal,
    legalities.gladiator_legal,
    legalities.pioneer_legal,
    legalities.explorer_legal,
    legalities.modern_legal,
    legalities.legacy_legal,
    legalities.pauper_legal,
    legalities.vintage_legal,
    legalities.penny_legal,
    legalities.commander_legal,
    legalities.oathbreaker_legal,
    legalities.standardbrawl_legal,
    legalities.brawl_legal,
    legalities.alchemy_legal,
    legalities.paupercommander_legal,
    legalities.duel_legal,
    legalities.oldschool_legal,
    legalities.premodern_legal,
    legalities.predh_legal

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

WHERE bp.price_eur IS NOT NULL

ORDER BY fc.card_id, bp.finish
"""


def load_price_dataframe() -> pd.DataFrame:
    """
    Load a dataframe from Postgres.

    Row grain:
        one row per card_id + finish price

    Target column:
        target_price_eur
    """
    sql_query = PRICE_DATAFRAME_SQL
    params = None

    conn = get_connection()

    try:
        df = pd.read_sql_query(
            sql_query,
            conn,
            params=params,
        )
    finally:
        conn.close()

    return df


def save_price_dataframe(
    output_path: str | Path | None = None,
) -> tuple[Path, int]:
    """
    Load the dataframe from Postgres and save it as a Parquet file.
    """
    if output_path is None:
        output_path = paths.dataframe_path

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_price_dataframe()

    if df.empty:
        raise ValueError("The price dataframe is empty. Check whether SQL price data exists.")

    df.to_parquet(
        output_path,
        index=False,
        engine="pyarrow",
    )
        
    return output_path, len(df)