# Utility Functions to transform the Data from the raw MongoDB and make it SQL ready
# raw_card -> transform_card(raw_card) -> structured payload -> postgres.py inserts it

def transform_card(raw_card: dict) -> dict:
    """Takes a raw MongoDB card document and returns a structured dictionary for SQL loading."""
    # Fact Tables
    card = {
        "card_id": raw_card.get("id"),
        "card_name": raw_card.get("name"),
        "reserved": raw_card.get("reserved"),
        "booster": raw_card.get("booster"),
        "digital": raw_card.get("digital"),
        "reprint": raw_card.get("reprint"),
        "edhrec_rank": raw_card.get("edhrec_rank"),
        "penny_rank": raw_card.get("penny_rank"),
        "full_art":raw_card.get("full_art"),
        "textless":raw_card.get("textless")
    }

    price_rows = []
    prices = raw_card.get("prices")
    price_nonfoil = prices.get("eur") if prices else None
    price_foil = prices.get("eur_foil") if prices else None
    if price_nonfoil:
        price_rows.append({"finish": "nonfoil", "price_eur": price_nonfoil})
    if price_foil:
        price_rows.append({"finish": "foil", "price_eur": price_foil})

    # Face logic and layout dimension

    layout = {
        "layout": raw_card.get("layout")
    }

    card_faces = {
        "card_faces": []
    }

    if layout["layout"] in ["split", "flip", "transform", "double_faced_token"]:
        for face in raw_card.get("card_faces", {}):
            card_face = {
                "face_name": face.get("name"),
                "face_mana_cost": face.get("mana_cost"),
                "face_type_line": face.get("type_line"),
                "face_oracle_text": face.get("oracle_text"),
                "face_power": face.get("power"),
                "face_toughness": face.get("toughness"),
                "face_loyalty": face.get("loyalty")
            }
            card_faces["card_faces"].append(card_face)

    # Dimensions
    type_line = {
        "type_line": raw_card.get("type_line")
    }
    mana_cost = {
        "mana_cost": raw_card.get("mana_cost")
    }
    release_date = {
        "release_date": raw_card.get("released_at")
    }
    language = {
        "language": raw_card.get("lang")
    }
    oracle_text = {
        "oracle_text": raw_card.get("oracle_text")
    }
    power = {
        "power": raw_card.get("power")
    }
    toughness = {
        "toughness": raw_card.get("toughness")
    },
    loyalty = {
        "loyalty": raw_card.get("loyalty")
    }
    set_dim = {
        "set": raw_card.get("set"),
        "set_name": raw_card.get("set_name"),
        "set_type": raw_card.get("set_type")
    }
    rarity = {
        "rarity": raw_card.get("rarity")
    }
    card_back_id = {
        "card_back_id":raw_card.get("card_back_id")
    }
    border_color = {
        "border_color":raw_card.get("border_color")
    }
    frame = {
        "frame":raw_card.get("frame")
    }

    # bridges
    artist = raw_card.get("artist")
    artists = [artist] if artist else []

    legalities = []
    legality_dic = raw_card.get("legalities", {})
    for format_name, legality in legality_dic.items():
        legalities.append({
            "format":format_name,
            "legality":legality
        })

    # Returned structure
    return {
        "card": card,
        "price_rows": price_rows,
        "dimensions": {
            "type_line": type_line,
            "mana_cost": mana_cost,
            "release_date": release_date,
            "language": language,
            "oracle_text": oracle_text,
            "power": power,
            "toughness": toughness,
            "loyalty": loyalty,
            "set": set_dim,
            "rarity": rarity,
            "card_back_id": card_back_id,
            "border_color": border_color,
            "frame":frame,
            "layout": layout
            },
        "bridges": {
            "colors": raw_card.get("colors") or [],
            "legalities": legalities,
            "keywords":raw_card.get("keywords") or [],
            "games":raw_card.get("games") or [],
            "artists": artists
            },
        "card_faces": {
            "card_faces": card_faces
        }
    }

def transform_core_card(raw_card: dict) -> dict:
    ...

def transform_dimensions(raw_card: dict) -> dict:
    ...

def transform_bridges(raw_card: dict) -> dict:
    ...

def clean_str(value):
    ...

def clean_int(value):
    ...

def clean_bool(value):
    ...

def clean_list(value):
    ...