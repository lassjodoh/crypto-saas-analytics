import os
import json
import random
from datetime import datetime, timedelta

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
from faker import Faker

load_dotenv(dotenv_path=".env")
fake = Faker()

BATCH_DIR = "batches"
STATE_FILE = "pipeline_state.json"

NEW_USERS_PER_RUN = 1
MIN_TRANSACTIONS = 20
MAX_TRANSACTIONS = 100
MIN_PRODUCT_USAGE = 20
MAX_PRODUCT_USAGE = 100
MIN_FEATURE_USAGE = 20
MAX_FEATURE_USAGE = 100
MAX_SUPPORT_TICKETS = 5


def get_snowflake_connection():
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )


def get_max_ids_from_snowflake():
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        queries = {
            "user_id": "SELECT COALESCE(MAX(USER_ID), 0) FROM BRONZE.USERS",
            "subscription_id": "SELECT COALESCE(MAX(SUBSCRIPTION_ID), 0) FROM BRONZE.SUBSCRIPTIONS",
            "transaction_id": "SELECT COALESCE(MAX(TRANSACTION_ID), 0) FROM BRONZE.TRANSACTIONS",
            "usage_id": "SELECT COALESCE(MAX(USAGE_ID), 0) FROM BRONZE.PRODUCT_USAGE",
            "feature_usage_id": "SELECT COALESCE(MAX(FEATURE_USAGE_ID), 0) FROM BRONZE.FEATURE_USAGE",
            "ticket_id": "SELECT COALESCE(MAX(TICKET_ID), 0) FROM BRONZE.SUPPORT_TICKETS"
        }

        max_ids = {}

        for key, query in queries.items():
            cursor.execute(query)
            max_ids[key] = int(cursor.fetchone()[0])

        return max_ids

    finally:
        cursor.close()
        conn.close()


def get_existing_active_subscriptions(limit=500):
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
            SELECT
                USER_ID,
                SUBSCRIPTION_ID,
                MONTHLY_FEE
            FROM BRONZE.SUBSCRIPTIONS
            WHERE SUBSCRIPTION_STATUS = 'Active'
            ORDER BY RANDOM()
            LIMIT {limit}
        """)

        rows = cursor.fetchall()

        return pd.DataFrame(
            rows,
            columns=["user_id", "subscription_id", "monthly_fee"]
        )

    finally:
        cursor.close()
        conn.close()


def get_existing_users(limit=500):
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
            SELECT USER_ID
            FROM BRONZE.USERS
            ORDER BY RANDOM()
            LIMIT {limit}
        """)

        rows = cursor.fetchall()

        return pd.DataFrame(rows, columns=["user_id"])

    finally:
        cursor.close()
        conn.close()


def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "last_run_number": 0,
            "last_generated_date": "2026-06-20",
            "last_batch_folder": "batches\\batch_0000"
        }

    with open(STATE_FILE, "r") as file:
        return json.load(file)


def save_state(state):
    with open(STATE_FILE, "w") as file:
        json.dump(state, file, indent=4)


def create_batch_folder(run_number):
    batch_name = f"batch_{run_number:04d}"
    batch_path = os.path.join(BATCH_DIR, batch_name)
    os.makedirs(batch_path, exist_ok=True)
    return batch_path, batch_name


def get_next_date(state):
    last_date = datetime.strptime(state["last_generated_date"], "%Y-%m-%d").date()
    return last_date + timedelta(days=1)


def generate_users(start_user_id, generated_date):
    countries = ["Canada", "United States", "United Kingdom", "Germany", "France"]
    channels = ["Organic Search", "Paid Ads", "Referral", "Social Media", "Email Campaign"]
    tiers = ["Basic", "Pro", "Enterprise"]
    statuses = ["Active", "Active", "Active", "Churned"]

    users = []

    for i in range(NEW_USERS_PER_RUN):
        users.append({
            "user_id": start_user_id + i + 1,
            "full_name": fake.name(),
            "email": fake.unique.email(),
            "signup_date": generated_date,
            "country": random.choice(countries),
            "acquisition_channel": random.choice(channels),
            "subscription_tier": random.choice(tiers),
            "status": random.choice(statuses)
        })

    return pd.DataFrame(users)


def generate_subscriptions(users_df, start_subscription_id):
    tier_prices = {
        "Basic": 29,
        "Pro": 45,
        "Enterprise": 79
    }

    subscriptions = []

    for i, (_, user) in enumerate(users_df.iterrows()):
        status = "Active"

        subscriptions.append({
            "subscription_id": start_subscription_id + i + 1,
            "user_id": user["user_id"],
            "plan_name": user["subscription_tier"],
            "monthly_fee": tier_prices[user["subscription_tier"]],
            "start_date": user["signup_date"],
            "end_date": None,
            "subscription_status": status
        })

    return pd.DataFrame(subscriptions)


def generate_transactions(subscriptions_pool_df, start_transaction_id, generated_date):
    transactions = []
    transaction_id = start_transaction_id

    payment_methods = ["Credit Card", "Debit Card", "PayPal", "Bank Transfer"]
    payment_statuses = ["Paid", "Paid", "Paid", "Failed"]

    transaction_count = random.randint(MIN_TRANSACTIONS, MAX_TRANSACTIONS)

    sampled = subscriptions_pool_df.sample(
        n=min(transaction_count, len(subscriptions_pool_df)),
        replace=len(subscriptions_pool_df) < transaction_count
    )

    for _, sub in sampled.iterrows():
        transaction_id += 1

        transactions.append({
            "transaction_id": transaction_id,
            "user_id": sub["user_id"],
            "subscription_id": sub["subscription_id"],
            "transaction_date": generated_date,
            "amount": sub["monthly_fee"],
            "payment_status": random.choice(payment_statuses),
            "payment_method": random.choice(payment_methods)
        })

    return pd.DataFrame(transactions), transaction_id


def generate_product_usage(users_pool_df, start_usage_id, generated_date):
    usage = []
    usage_id = start_usage_id
    activity_month = generated_date.strftime("%Y-%m")

    usage_count = random.randint(MIN_PRODUCT_USAGE, MAX_PRODUCT_USAGE)

    sampled = users_pool_df.sample(
        n=min(usage_count, len(users_pool_df)),
        replace=len(users_pool_df) < usage_count
    )

    for _, user in sampled.iterrows():
        usage_id += 1

        usage.append({
            "usage_id": usage_id,
            "user_id": user["user_id"],
            "activity_month": activity_month,
            "login_count": random.randint(1, 25),
            "dashboards_viewed": random.randint(1, 60),
            "reports_generated": random.randint(0, 20),
            "api_calls": random.randint(0, 5000),
            "session_minutes": random.randint(5, 500)
        })

    return pd.DataFrame(usage), usage_id


def generate_feature_usage(users_pool_df, start_feature_usage_id, generated_date):
    feature_usage = []
    feature_usage_id = start_feature_usage_id
    usage_month = generated_date.strftime("%Y-%m")

    features = [
        "Price Alerts",
        "Auto Invest",
        "Portfolio Insights",
        "Risk Dashboard",
        "API Access"
    ]

    feature_count = random.randint(MIN_FEATURE_USAGE, MAX_FEATURE_USAGE)

    sampled = users_pool_df.sample(
        n=min(feature_count, len(users_pool_df)),
        replace=len(users_pool_df) < feature_count
    )

    for _, user in sampled.iterrows():
        feature_usage_id += 1

        feature_usage.append({
            "feature_usage_id": feature_usage_id,
            "user_id": user["user_id"],
            "feature_name": random.choice(features),
            "usage_month": usage_month,
            "usage_count": random.randint(1, 20)
        })

    return pd.DataFrame(feature_usage), feature_usage_id


def generate_support_tickets(users_pool_df, start_ticket_id, generated_date):
    tickets = []
    ticket_id = start_ticket_id

    categories = ["Billing", "Login Issue", "Trading Issue", "Account Verification", "Technical Support"]
    priorities = ["Low", "Medium", "High"]
    statuses = ["Open", "Resolved", "Resolved", "Closed"]

    ticket_count = random.randint(0, MAX_SUPPORT_TICKETS)

    if ticket_count == 0:
        return pd.DataFrame(columns=[
            "ticket_id",
            "user_id",
            "ticket_date",
            "category",
            "priority",
            "status",
            "resolution_hours"
        ]), ticket_id

    sampled = users_pool_df.sample(
        n=min(ticket_count, len(users_pool_df)),
        replace=len(users_pool_df) < ticket_count
    )

    for _, user in sampled.iterrows():
        ticket_id += 1

        tickets.append({
            "ticket_id": ticket_id,
            "user_id": user["user_id"],
            "ticket_date": generated_date,
            "category": random.choice(categories),
            "priority": random.choice(priorities),
            "status": random.choice(statuses),
            "resolution_hours": random.randint(1, 120)
        })

    return pd.DataFrame(tickets), ticket_id


def save_csv(df, batch_path, file_name):
    file_path = os.path.join(batch_path, file_name)
    df.to_csv(file_path, index=False)
    print(f"Created {file_path}: {len(df)} rows")


if __name__ == "__main__":
    state = load_state()

    last_run_number = state.get("last_run_number", 0)
    new_run_number = last_run_number + 1
    generated_date = get_next_date(state)

    batch_path, batch_name = create_batch_folder(new_run_number)

    print(f"Generating {batch_name} for {generated_date}...")

    max_ids = get_max_ids_from_snowflake()

    print("Starting IDs from Snowflake:")
    print(max_ids)

    users_df = generate_users(
        start_user_id=max_ids["user_id"],
        generated_date=generated_date
    )

    subscriptions_df = generate_subscriptions(
        users_df=users_df,
        start_subscription_id=max_ids["subscription_id"]
    )

    existing_subscriptions_df = get_existing_active_subscriptions(limit=500)
    existing_users_df = get_existing_users(limit=500)

    subscriptions_pool_df = pd.concat(
        [
            existing_subscriptions_df,
            subscriptions_df[["user_id", "subscription_id", "monthly_fee"]]
        ],
        ignore_index=True
    )

    users_pool_df = pd.concat(
        [
            existing_users_df,
            users_df[["user_id"]]
        ],
        ignore_index=True
    )

    transactions_df, _ = generate_transactions(
        subscriptions_pool_df=subscriptions_pool_df,
        start_transaction_id=max_ids["transaction_id"],
        generated_date=generated_date
    )

    product_usage_df, _ = generate_product_usage(
        users_pool_df=users_pool_df,
        start_usage_id=max_ids["usage_id"],
        generated_date=generated_date
    )

    feature_usage_df, _ = generate_feature_usage(
        users_pool_df=users_pool_df,
        start_feature_usage_id=max_ids["feature_usage_id"],
        generated_date=generated_date
    )

    support_tickets_df, _ = generate_support_tickets(
        users_pool_df=users_pool_df,
        start_ticket_id=max_ids["ticket_id"],
        generated_date=generated_date
    )

    save_csv(users_df, batch_path, "users.csv")
    save_csv(subscriptions_df, batch_path, "subscriptions.csv")
    save_csv(transactions_df, batch_path, "transactions.csv")
    save_csv(product_usage_df, batch_path, "product_usage.csv")
    save_csv(feature_usage_df, batch_path, "feature_usage.csv")
    save_csv(support_tickets_df, batch_path, "support_tickets.csv")

    state["last_run_number"] = new_run_number
    state["last_generated_date"] = generated_date.strftime("%Y-%m-%d")
    state["last_batch_folder"] = batch_path

    save_state(state)

    print(f"{batch_name} generated successfully.")
    print(f"Batch folder: {batch_path}")