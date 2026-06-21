import os
import json
import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

fake = Faker()

BATCH_DIR = "batches"
STATE_FILE = "pipeline_state.json"


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


def generate_users(start_user_id, batch_size, generated_date):
    users = []

    countries = ["Canada", "United States", "United Kingdom", "Germany", "France"]
    channels = ["Organic Search", "Paid Ads", "Referral", "Social Media", "Email Campaign"]
    tiers = ["Basic", "Pro", "Enterprise"]
    statuses = ["Active", "Active", "Active", "Churned"]

    for i in range(batch_size):
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
    subscriptions = []

    tier_prices = {
        "Basic": 29,
        "Pro": 45,
        "Enterprise": 79
    }

    statuses = ["Active", "Active", "Active", "Churned"]

    for i, (_, user) in enumerate(users_df.iterrows()):
        status = random.choice(statuses)

        subscriptions.append({
            "subscription_id": start_subscription_id + i + 1,
            "user_id": user["user_id"],
            "plan_name": user["subscription_tier"],
            "monthly_fee": tier_prices[user["subscription_tier"]],
            "start_date": user["signup_date"],
            "end_date": "" if status == "Active" else user["signup_date"],
            "subscription_status": status
        })

    return pd.DataFrame(subscriptions)


def generate_transactions(subscriptions_df, start_transaction_id, generated_date):
    transactions = []
    transaction_id = start_transaction_id

    payment_methods = ["Credit Card", "Debit Card", "PayPal", "Bank Transfer"]
    payment_statuses = ["Paid", "Paid", "Paid", "Failed"]

    for _, sub in subscriptions_df.iterrows():
        for _ in range(random.randint(1, 4)):
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


def generate_product_usage(users_df, start_usage_id, generated_date):
    usage = []
    usage_id = start_usage_id

    activity_month = generated_date.strftime("%Y-%m")

    for _, user in users_df.iterrows():
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


def generate_feature_usage(users_df, start_feature_usage_id, generated_date):
    feature_usage = []
    feature_usage_id = start_feature_usage_id

    features = [
        "Price Alerts",
        "Auto Invest",
        "Portfolio Insights",
        "Risk Dashboard",
        "API Access"
    ]

    usage_month = generated_date.strftime("%Y-%m")

    for _, user in users_df.iterrows():
        for _ in range(random.randint(1, 4)):
            feature_usage_id += 1

            feature_usage.append({
                "feature_usage_id": feature_usage_id,
                "user_id": user["user_id"],
                "feature_name": random.choice(features),
                "usage_month": usage_month,
                "usage_count": random.randint(1, 20)
            })

    return pd.DataFrame(feature_usage), feature_usage_id


def generate_support_tickets(users_df, start_ticket_id, generated_date):
    tickets = []
    ticket_id = start_ticket_id

    categories = ["Billing", "Login Issue", "Trading Issue", "Account Verification", "Technical Support"]
    priorities = ["Low", "Medium", "High"]
    statuses = ["Open", "Resolved", "Resolved", "Closed"]

    sampled_users = users_df.sample(frac=0.25) if len(users_df) > 0 else users_df

    for _, user in sampled_users.iterrows():
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

    batch_size = random.randint(10, 30)

    start_user_id = 2150 + (last_run_number * 30)
    start_subscription_id = 2150 + (last_run_number * 30)
    start_transaction_id = 28212 + (last_run_number * 120)
    start_usage_id = 30475 + (last_run_number * 30)
    start_feature_usage_id = 75996 + (last_run_number * 90)
    start_ticket_id = 5301 + (last_run_number * 10)

    users_df = generate_users(start_user_id, batch_size, generated_date)

    subscriptions_df = generate_subscriptions(
        users_df,
        start_subscription_id
    )

    transactions_df, _ = generate_transactions(
        subscriptions_df,
        start_transaction_id,
        generated_date
    )

    product_usage_df, _ = generate_product_usage(
        users_df,
        start_usage_id,
        generated_date
    )

    feature_usage_df, _ = generate_feature_usage(
        users_df,
        start_feature_usage_id,
        generated_date
    )

    support_tickets_df, _ = generate_support_tickets(
        users_df,
        start_ticket_id,
        generated_date
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