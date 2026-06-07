from pydantic import BaseModel

ALLOWED_LEGALITY_FORMATS = {
    "standard_legal",
    "future_legal",
    "historic_legal",
    "timeless_legal",
    "gladiator_legal",
    "pioneer_legal",
    "explorer_legal",
    "modern_legal",
    "legacy_legal",
    "pauper_legal",
    "vintage_legal",
    "penny_legal",
    "commander_legal",
    "oathbreaker_legal",
    "standardbrawl_legal",
    "brawl_legal",
    "alchemy_legal",
    "paupercommander_legal",
    "duel_legal",
    "oldschool_legal",
    "premodern_legal",
    "predh_legal",
}

ALLOWED_LEGALITY_VALUES = {
    "legal",
    "not_legal",
    "banned",
    "restricted",
}

class HealthResponse(BaseModel):
    status : str

class PredictPriceRequest(BaseModel):
    finish : str = "nonfoil"
    language : str = "en"
    set_type : str = "expansion"
    rarity : str = "rare"
    border_color : str = "black"
    frame : str = "2015"
    layout : str = "normal"
    colors : list[str] = []
    games : list[str] = ["paper"]
    power : str = ""
    toughness : str = ""
    loyalty : str = ""
    edhrec_rank : int | None = None
    penny_rank : int | None = None
    reserved : bool = False
    booster : bool = True
    digital : bool = False
    reprint: bool = False
    full_art : bool = False
    textless : bool = False
    legalities: dict[str, str] = {}


class PredictPriceResponse(BaseModel):
    predicted_price_eur : float