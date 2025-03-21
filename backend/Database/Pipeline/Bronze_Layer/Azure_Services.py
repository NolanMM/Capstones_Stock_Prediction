from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from io import StringIO
import pandas as pd
import os

load_dotenv("./Bronze_Layer/.env", override=True)

CONNECTION_STRING_BRONE_STORAGE = os.getenv("CONNECTION_STRING_BRONE_STORAGE")
CONTAINER_NAME_BRONZE_STORAGE = os.getenv("CONTAINER_NAME_BRONZE_STORAGE")

def write_dataframe_to_blob(df, blob_name):
    try:
        # Convert DataFrame to CSV format in memory
        if not isinstance(df, pd.DataFrame):
            df = df.to_pandas()
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        # Connect to Blob Storage
        service = BlobServiceClient.from_connection_string(CONNECTION_STRING_BRONE_STORAGE)
        container_client = service.get_container_client(CONTAINER_NAME_BRONZE_STORAGE)
        
        # Upload the CSV file to Blob Storage
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(csv_buffer.getvalue(), overwrite=True)
        
        print(f"Successfully uploaded {blob_name} to {CONTAINER_NAME_BRONZE_STORAGE}")
    except Exception as ex:
        print("Exception:", ex)

# # Write the DataFrame to Blob
# write_dataframe_to_blob(df, blob_name)