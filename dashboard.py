import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

import os

# ----------------------------
# DB Connection
# ----------------------------
DDB_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DB_URL,
    connect_args={
        "sslmode": "require",
        "application_name": "streamlit",
        "options": "-c inet_client_addr=0.0.0.0"
    }
)
# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(page_title="NYC Taxi Analytics – Dec 2024", layout="wide")
st.title("🚖 NYC Taxi Analytics – December 2024")

# ----------------------------
# Load Data
# ----------------------------
@st.cache_data
def load_table(table_name):
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)

daily_revenue = load_table("daily_revenue")
payment_summary = load_table("payment_summary")
passenger_summary = load_table("passenger_summary")
pickup_summary = load_table("pickup_summary")
dropoff_summary = load_table("dropoff_summary")
hourly_trends = load_table("hourly_trends")
trip_length_summary = load_table("trip_length_summary")
outliers = load_table("outliers")

# ----------------------------
# KPIs
# ----------------------------
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Total Trips", f"{daily_revenue['trips'].sum():,}")
kpi2.metric("Total Revenue", f"${daily_revenue['total_revenue'].sum():,.2f}")
kpi3.metric("Avg Fare", f"${daily_revenue['avg_fare'].mean():.2f}")
kpi4.metric("Avg Distance", f"{daily_revenue['avg_distance'].mean():.2f} mi")
kpi5.metric("Avg Tip %", f"{daily_revenue['avg_tip_pct'].mean():.2f}%")

st.markdown("---")

# ----------------------------
# Daily Trends
# ----------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Daily Revenue Trend")
    st.line_chart(daily_revenue.set_index("trip_date")["total_revenue"])

with col2:
    st.subheader("📊 Daily Trips Trend")
    st.line_chart(daily_revenue.set_index("trip_date")["trips"])

# ----------------------------
# Payment & Passenger Behavior
# ----------------------------
st.subheader("💳 Revenue by Payment Type")
st.bar_chart(payment_summary.set_index("payment_type")["revenue"])

st.subheader("🧑‍🤝‍🧑 Trips by Passenger Count")
st.bar_chart(passenger_summary.set_index("passenger_count")["trips"])

st.subheader("🚗 Trip Length Distribution")
st.bar_chart(trip_length_summary.set_index("trip_bucket")["trips"])

# ----------------------------
# Geography
# ----------------------------
st.subheader("📍 Top 10 Pickup Zones by Revenue")
top_pickups = pickup_summary.sort_values("revenue", ascending=False).head(10)
st.bar_chart(top_pickups.set_index("pickup_zone")["revenue"])

st.subheader("🏁 Top 10 Dropoff Zones by Revenue")
top_dropoffs = dropoff_summary.sort_values("revenue", ascending=False).head(10)
st.bar_chart(top_dropoffs.set_index("dropoff_zone")["revenue"])

# ----------------------------
# Hourly Trends
# ----------------------------
st.subheader("🕑 Trips by Hour of Day")
st.line_chart(hourly_trends.set_index("hour_of_day")["trips"])

# ----------------------------
# Outliers
# ----------------------------
st.subheader("⚠️ Outlier Rides (Top 50)")
st.dataframe(outliers.head(50))
