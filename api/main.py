from fastapi import FastAPI, HTTPException
from api.schemas import HealthResponse, PredictPriceRequest, PredictPriceResponse, ALLOWED_LEGALITY_FORMATS, ALLOWED_LEGALITY_VALUES
from cli.lib.ml_pipeline import predict_card_price

api = FastAPI()
@api.get('/health', response_model = HealthResponse)
def get_healthcheck():
    return HealthResponse(status="ok")

@api.post('/predict-price', response_model = PredictPriceResponse)
def post_predict_price(req : PredictPriceRequest):
    card_features = {
        "finish": req.finish,
        "language": req.language,
        "set_type": req.set_type,
        "rarity": req.rarity,
        "border_color": req.border_color,
        "frame": req.frame,
        "layout": req.layout,
        "colors": req.colors,
        "games": req.games,
        "power": req.power or None,
        "toughness": req.toughness or None,
        "loyalty": req.loyalty or None,
        "edhrec_rank": req.edhrec_rank,
        "penny_rank": req.penny_rank,
        "reserved": req.reserved,
        "booster": req.booster,
        "digital": req.digital,
        "reprint": req.reprint,
        "full_art": req.full_art,
        "textless": req.textless,
    }
    for key, item in req.legalities.items():
        if key in ALLOWED_LEGALITY_FORMATS and item in ALLOWED_LEGALITY_VALUES:
            card_features[key] = item
        else:
            raise HTTPException(status_code=400, detail=f"{key} or {item} are not allowed values for legalities. Check the API Documentation for help!")
    try:
        predicted_price_eur = predict_card_price(card_features)
        return PredictPriceResponse(predicted_price_eur=predicted_price_eur)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No Model available to predict")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to predict Price")