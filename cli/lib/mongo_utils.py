from pymongo import MongoClient

client = MongoClient(
    host="127.0.0.1",
    port=27017,
    username="root",
    password="rootpassword",
    authSource="admin"
)

db = client["raw_scryfall"]

print(db["cards"].find_one())