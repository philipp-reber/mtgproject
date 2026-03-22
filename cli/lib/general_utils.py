from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "scryfall_all_cards.json"
RAW_META_PATH = PROJECT_ROOT / "data" / "raw" / "scryfall_all_cards.meta.json"
BULK_DATA_URL = "https://api.scryfall.com/bulk-data"