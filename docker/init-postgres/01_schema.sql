CREATE TABLE IF NOT EXISTS dim_type_line (
    id SERIAL PRIMARY KEY,
    type_line TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_mana_cost (
    id SERIAL PRIMARY KEY,
    mana_cost TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_release_date (
    id SERIAL PRIMARY KEY,
    release_date DATE UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_language (
    id SERIAL PRIMARY KEY,
    language TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_oracle_text (
    id SERIAL PRIMARY KEY,
    oracle_text TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_power (
    id SERIAL PRIMARY KEY,
    power TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_toughness (
    id SERIAL PRIMARY KEY,
    toughness TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_loyalty (
    id SERIAL PRIMARY KEY,
    loyalty TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_set (
    id SERIAL PRIMARY KEY,
    set_code TEXT UNIQUE,
    set_name TEXT,
    set_type TEXT
);

CREATE TABLE IF NOT EXISTS dim_rarity (
    id SERIAL PRIMARY KEY,
    rarity TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_border_color (
    id SERIAL PRIMARY KEY,
    border_color TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_frame (
    id SERIAL PRIMARY KEY,
    frame TEXT UNIQUE
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
    release_date_id INTEGER REFERENCES dim_release_date(id),
    language_id INTEGER REFERENCES dim_language(id),
    oracle_text_id INTEGER REFERENCES dim_oracle_text(id),
    power_id INTEGER REFERENCES dim_power(id),
    toughness_id INTEGER REFERENCES dim_toughness(id),
    loyalty_id INTEGER REFERENCES dim_loyalty(id),
    set_id INTEGER REFERENCES dim_set(id),
    rarity_id INTEGER REFERENCES dim_rarity(id),
    border_color_id INTEGER REFERENCES dim_border_color(id),
    frame_id INTEGER REFERENCES dim_frame(id),
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

CREATE TABLE IF NOT EXISTS card_faces (
    card_id TEXT REFERENCES fact_cards(card_id) ON DELETE CASCADE,
    face_index INTEGER NOT NULL,
    face_name TEXT,
    face_mana_cost TEXT,
    face_type_line TEXT,
    face_oracle_text TEXT,
    face_power TEXT,
    face_toughness TEXT,
    face_loyalty TEXT,
    UNIQUE (card_id, face_index)
);