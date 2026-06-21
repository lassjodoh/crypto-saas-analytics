import os
import glob
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

load_dotenv(dotenv_path=".env")

BATCH_DIR = "batches"

csv_to_table = {
    "users.csv": "USERS",
    "subscriptions.csv": "SUBSCRIPTIONS",
    "transactions.csv": "TRANSACTIONS",
    "product_usage.csv": "PRODUCT_USAGE",
    "feature_usage.csv": "FEATURE_USAGE",
    "support_tickets.csv": "SUPPORT_TICKETS"
}


def get_latest_batch_folder():
    batch_folders = glob.glob(os.path.join(BATCH_DIR, "batch_*"))

    if not batch_folders:
        raise FileNotFoundError("No batch folders found.")

    return max(batch_folders)


conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA")
)

print("Connected to Snowflake.")

latest_batch = get_latest_batch_folder()
print(f"Loading latest batch: {latest_batch}")

for csv_file, table_name in csv_to_table.items():
    file_path = os.path.join(latest_batch, csv_file)

    if not os.path.exists(file_path):
        print(f"Skipping {csv_file} — not found in batch.")
        continue

    df = pd.read_csv(file_path)
    df.columns = [col.upper() for col in df.columns]

    success, nchunks, nrows, _ = write_pandas(
        conn,
        df,
        table_name,
        auto_create_table=False,
        overwrite=False
    )

    print(f"{table_name}: inserted {nrows} rows")

conn.close()
print("Incremental batch loaded successfully.")