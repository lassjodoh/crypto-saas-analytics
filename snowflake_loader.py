import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv
import os



load_dotenv(dotenv_path=".env")

print("Account:", os.getenv("SNOWFLAKE_ACCOUNT"))
print("User:", os.getenv("SNOWFLAKE_USER"))
print("Database:", os.getenv("SNOWFLAKE_DATABASE"))

conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA")
)
print("Connected successfully!")



csv_files = {
    "USERS": "data/users.csv",
    "SUBSCRIPTIONS": "data/subscriptions.csv",
    "TRANSACTIONS": "data/transactions.csv",
    "PRODUCT_USAGE": "data/product_usage.csv",
    "FEATURE_USAGE": "data/feature_usage.csv",
    "SUPPORT_TICKETS": "data/support_tickets.csv"
}

for table_name, file_path in csv_files.items():
    df = pd.read_csv(file_path)

    df.columns = [col.upper() for col in df.columns]

    cursor = conn.cursor()
    cursor.execute(f"CREATE OR REPLACE TABLE {table_name} LIKE {table_name}") if False else None

    success, nchunks, nrows, _ = write_pandas(
        conn,
        df,
        table_name,
        auto_create_table=True,
        overwrite=True
    )

    print(f"{table_name}: loaded {nrows} rows")

conn.close()
print("All Bronze tables loaded successfully!")