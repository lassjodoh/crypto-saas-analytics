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


def get_batch_name(batch_folder):
    return os.path.basename(batch_folder)


def ensure_batch_log_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS BATCH_LOAD_LOG (
            BATCH_NAME STRING,
            LOAD_STARTED_AT TIMESTAMP,
            LOAD_COMPLETED_AT TIMESTAMP,
            STATUS STRING,
            ROWS_LOADED NUMBER
        )
    """)


def batch_already_loaded(cursor, batch_name):
    cursor.execute("""
        SELECT COUNT(*)
        FROM BATCH_LOAD_LOG
        WHERE BATCH_NAME = %s
          AND STATUS = 'SUCCESS'
    """, (batch_name,))

    return cursor.fetchone()[0] > 0


def insert_batch_start(cursor, batch_name):
    cursor.execute("""
        INSERT INTO BATCH_LOAD_LOG (
            BATCH_NAME,
            LOAD_STARTED_AT,
            STATUS,
            ROWS_LOADED
        )
        VALUES (%s, CURRENT_TIMESTAMP, 'STARTED', 0)
    """, (batch_name,))


def update_batch_success(cursor, batch_name, rows_loaded):
    cursor.execute("""
        INSERT INTO BATCH_LOAD_LOG (
            BATCH_NAME,
            LOAD_STARTED_AT,
            LOAD_COMPLETED_AT,
            STATUS,
            ROWS_LOADED
        )
        VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'SUCCESS', %s)
    """, (batch_name, rows_loaded))


def update_batch_failed(cursor, batch_name):
    cursor.execute("""
        INSERT INTO BATCH_LOAD_LOG (
            BATCH_NAME,
            LOAD_STARTED_AT,
            LOAD_COMPLETED_AT,
            STATUS,
            ROWS_LOADED
        )
        VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'FAILED', 0)
    """, (batch_name,))


conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA")
)

cursor = conn.cursor()

try:
    print("Connected to Snowflake.")

    ensure_batch_log_table(cursor)

    latest_batch = get_latest_batch_folder()
    batch_name = get_batch_name(latest_batch)

    print(f"Latest batch: {batch_name}")

    if batch_already_loaded(cursor, batch_name):
        print(f"{batch_name} has already been loaded. Skipping.")
    else:
        insert_batch_start(cursor, batch_name)

        total_rows_loaded = 0

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

            total_rows_loaded += nrows

            print(f"{table_name}: inserted {nrows} rows")

        update_batch_success(cursor, batch_name, total_rows_loaded)

        print(f"{batch_name} loaded successfully.")
        print(f"Total rows loaded: {total_rows_loaded}")

except Exception as e:
    print(f"Load failed: {e}")

    try:
        update_batch_failed(cursor, batch_name)
    except Exception:
        pass

finally:
    cursor.close()
    conn.close()
    print("Snowflake connection closed.")