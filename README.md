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