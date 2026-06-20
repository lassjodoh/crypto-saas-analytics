import pandas as pd
import random
from faker import Faker
from datetime import date

fake = Faker()

random.seed(42)
Faker.seed(42)

customer_growth = {
    2024: 400,
    2025: 750,
    2026: 1000
}

countries = [
    "Canada",
    "United States",
    "United Kingdom",
    "Australia",
    "Germany"
]

channels = [
    "Organic Search",
    "Referral",
    "Social Media",
    "Paid Ads",
    "Partner Program"
]

tiers = ["Basic", "Pro", "Enterprise"]

users = []
user_id = 1

for year, customer_count in customer_growth.items():

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    for _ in range(customer_count):

        signup_date = fake.date_between(
            start_date=start_date,
            end_date=end_date
        )

        users.append({
            "user_id": user_id,
            "full_name": fake.name(),
            "email": fake.email(),
            "signup_date": signup_date,
            "country": random.choice(countries),
            "acquisition_channel": random.choices(
                channels,
                weights=[35, 25, 20, 15, 5]
            )[0],
            "subscription_tier": random.choices(
                tiers,
                weights=[60, 30, 10]
            )[0],
            "status": random.choices(
                ["Active", "Churned"],
                weights=[85, 15]
            )[0]
        })

        user_id += 1

users_df = pd.DataFrame(users)

users_df.to_csv("data/users.csv", index=False)

print(users_df.head())
print(f"Total users generated: {len(users_df)}")




# Create subscriptions dataset

plan_prices = {
    "Basic": 29,
    "Pro": 45,
    "Enterprise": 79
}

subscriptions = []
subscription_id = 1

for _, user in users_df.iterrows():

    start_date = user["signup_date"]

    if user["status"] == "Churned":
        end_date = fake.date_between(
            start_date=start_date,
            end_date=date(2026, 12, 31)
        )
        subscription_status = "Cancelled"
    else:
        end_date = None
        subscription_status = "Active"

    subscriptions.append({
        "subscription_id": subscription_id,
        "user_id": user["user_id"],
        "plan_name": user["subscription_tier"],
        "monthly_fee": plan_prices[user["subscription_tier"]],
        "start_date": start_date,
        "end_date": end_date,
        "subscription_status": subscription_status
    })

    subscription_id += 1

subscriptions_df = pd.DataFrame(subscriptions)

subscriptions_df.to_csv(
    "data/subscriptions.csv",
    index=False
)

print(f"Total subscriptions generated: {len(subscriptions_df)}")



# Generate product usage dataset

usage_records = []
usage_id = 1

for _, user in users_df.iterrows():

    usage_start_date = user["signup_date"]
    usage_end_date = date(2026, 12, 31)

    activity_dates = pd.date_range(
        start=usage_start_date,
        end=usage_end_date,
        freq="MS"
    )

    for activity_date in activity_dates:

        usage_records.append({
            "usage_id": usage_id,
            "user_id": user["user_id"],
            "activity_month": activity_date.date(),
            "login_count": random.randint(2, 30),
            "dashboards_viewed": random.randint(1, 80),
            "reports_generated": random.randint(0, 25),
            "api_calls": random.randint(0, 1000),
            "session_minutes": random.randint(10, 900)
        })

        usage_id += 1

product_usage_df = pd.DataFrame(usage_records)

product_usage_df.to_csv(
    "data/product_usage.csv",
    index=False
)

print(f"Total product usage records generated: {len(product_usage_df)}")



# Generate transactions dataset

payment_methods = [
    "Credit Card",
    "Debit Card",
    "PayPal",
    "Bank Transfer"
]

transactions = []
transaction_id = 1

for _, subscription in subscriptions_df.iterrows():

    transaction_start_date = subscription["start_date"]

    if subscription["subscription_status"] == "Cancelled":
        transaction_end_date = subscription["end_date"]
    else:
        transaction_end_date = date(2026, 12, 31)

    payment_dates = pd.date_range(
        start=transaction_start_date,
        end=transaction_end_date,
        freq="MS"
    )

    for payment_date in payment_dates:

        transactions.append({
            "transaction_id": transaction_id,
            "user_id": subscription["user_id"],
            "subscription_id": subscription["subscription_id"],
            "transaction_date": payment_date.date(),
            "amount": subscription["monthly_fee"],
            "payment_status": random.choices(
                ["Successful", "Failed"],
                weights=[95, 5]
            )[0],
            "payment_method": random.choice(payment_methods)
        })

        transaction_id += 1

transactions_df = pd.DataFrame(transactions)

transactions_df.to_csv(
    "data/transactions.csv",
    index=False
)

print(f"Total transactions generated: {len(transactions_df)}")



# Generate support tickets dataset

ticket_categories = [
    "Billing",
    "API Issues",
    "Login Problems",
    "Dashboard Errors",
    "Feature Request",
    "Account Management"
]

ticket_priorities = [
    "Low",
    "Medium",
    "High",
    "Critical"
]

ticket_statuses = [
    "Resolved",
    "In Progress",
    "Open"
]

tickets = []
ticket_id = 1

for _, user in users_df.iterrows():

    num_tickets = random.randint(0, 5)

    for _ in range(num_tickets):

        ticket_date = fake.date_between(
            start_date=user["signup_date"],
            end_date=date(2026, 12, 31)
        )

        tickets.append({
            "ticket_id": ticket_id,
            "user_id": user["user_id"],
            "ticket_date": ticket_date,
            "category": random.choice(ticket_categories),
            "priority": random.choices(
                ticket_priorities,
                weights=[40, 35, 20, 5]
            )[0],
            "status": random.choices(
                ticket_statuses,
                weights=[80, 10, 10]
            )[0],
            "resolution_hours": random.randint(1, 72)
        })

        ticket_id += 1

support_tickets_df = pd.DataFrame(tickets)

support_tickets_df.to_csv("data/support_tickets.csv", index=False)

print(
    f"Total support tickets generated: {len(support_tickets_df)}"
)



# Generate feature usage dataset

features = [
    "Portfolio Tracker",
    "Trading Signals",
    "Risk Analytics",
    "Market Scanner",
    "API Access",
    "Custom Dashboards"
]

feature_usage = []
feature_usage_id = 1

for _, user in users_df.iterrows():

    usage_start_date = user["signup_date"]
    usage_end_date = date(2026, 12, 31)

    feature_dates = pd.date_range(
        start=usage_start_date,
        end=usage_end_date,
        freq="MS"
    )

    for feature_date in feature_dates:

        selected_features = random.sample(
            features,
            random.randint(1, 4)
        )

        for feature in selected_features:

            feature_usage.append({
                "feature_usage_id": feature_usage_id,
                "user_id": user["user_id"],
                "feature_name": feature,
                "usage_month": feature_date.date(),
                "usage_count": random.randint(1, 50)
            })

            feature_usage_id += 1

feature_usage_df = pd.DataFrame(feature_usage)

feature_usage_df.to_csv("data/feature_usage.csv", index=False)

print(f"Total feature usage records generated: {len(feature_usage_df)}")



print(users_df.head())
print(subscriptions_df.head())
print(product_usage_df.head())
print(transactions_df.head())
print(support_tickets_df.head())
print(feature_usage_df.head())