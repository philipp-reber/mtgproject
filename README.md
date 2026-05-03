# MTG DataEngineering and price prediction project

## 1. Set-Up

The Project includes a client for executing all necessary commands.

Install all the requirements from requirements.txt

Please create a .env file filling out the following information:

MONGO_HOST=
MONGO_PORT=
MONGO_USERNAME=
MONGO_PASSWORD=
MONGO_AUTH_SOURCE=
MONGO_DATABASE=
MONGO_COLLECTION=
MONGO_CONTAINER_NAME=
MONGO_IMPORT_MOUNT_PATH=

POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_CONTAINER_NAME=

PIPELINE_BATCH_SIZE=
SCRYFALL_BULK_DATA_URL=https://api.scryfall.com/bulk-data

Run the command "checkstatus" and the consecutive commands suggested to start up the infrastructure. Afterwards you can use the other commands.

Example for the SQL Loader logic:

[
    Lightning Bolt,
    Llanowar Elves,
    Sol Ring,
]

1. Extract type lines:
   Instant
   Creature — Elf Druid
   Artifact

2. Insert missing type lines into dim_type_line.

3. Fetch type_line IDs:
   Instant -> 1
   Creature — Elf Druid -> 2
   Artifact -> 3

4. Extract mana costs:
   {R}
   {G}
   {1}

5. Insert missing mana costs into dim_mana_cost.

6. Fetch mana_cost IDs:
   {R} -> 1
   {G} -> 2
   {1} -> 3

7. Repeat for rarity, layout, frame, language, etc.

8. Build fact_cards rows:
   Lightning Bolt uses type_line_id=1, mana_cost_id=1
   Llanowar Elves uses type_line_id=2, mana_cost_id=2
   Sol Ring uses type_line_id=3, mana_cost_id=3

9. Delete old bridge rows for those three card IDs.

10. Insert fact rows.

11. Insert bridge rows:
    Lightning Bolt -> color R
    Llanowar Elves -> color G
    Sol Ring -> maybe no colors
    games, legalities, prices, artists, etc.

12. Commit.