pip install -r database_requirements.txt
Configure the .env file in /backend/Database/Pipeline/Bronze_Layer/.env for

API_KEY_FMP=""
CONTAINER_NAME_BRONZE_STORAGE=""
CONNECTION_STRING_BRONE_STORAGE=""

prefect server start
$env:PREFECT_API_URL="http://127.0.0.1:4200/api";

In Database Directory
python .\Bronze_Layer_Flows.py