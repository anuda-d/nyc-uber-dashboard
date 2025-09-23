# dashboard.py
# -----------------------------------------------------------------------------
# NYC Taxi Analytics – Streamlit Dashboard
# Uses Supabase (Postgres) as the warehouse and queries summary views created
# in your pipeline (daily_revenue, payment_summary, passenger_summary, etc.).

# Notes:
# - The app reads DATABASE_URL from environment variables (Streamlit Secrets).
# - All charts use Plotly for better interactivity.
# - Tables use pre-aggregated, rounded summary views to keep visuals clean.
# -----------------------------------------------------------------------------

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
import plotly.express as px

# -----------------------------------------------------------------------------
# Database connection
# -----------------------------------------------------------------------------
# Expecting DATABASE_URL in the environment (e.g., Streamlit Cloud secrets).
# For local dev, export DATABASE_URL with your Supabase pooler URL.
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    st.error("DATABASE_URL is not set. Please configure it in your environment or Streamlit secrets.")
    st.stop()

# Create engine for querying Supabase Postgres (via pooler endpoint)
engine = create_engine(DB_URL)

# -----------------------------------------------------------------------------
# Data loading helpers
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_table(table_name: str) -> pd.DataFrame:
    """
    Load a table or materialized view into a Pandas DataFrame.
    Cached for performance; invalidate cache by changing code or clearing cache.
    """
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)

# Preload all summary views (created by your pipeline)
daily_revenue       = load_table("daily_revenue")
payment_summary     = load_table("payment_summary")
passenger_summary   = load_table("passenger_summary")
pickup_summary      = load_table("pickup_summary")
dropoff_summary     = load_table("dropoff_summary")
hourly_trends       = load_table("hourly_trends")
trip_length_summary = load_table("trip_length_summary")
# outliers view intentionally not used (replaced with Performance Insights)

# -----------------------------------------------------------------------------
# Global page config
# -----------------------------------------------------------------------------
st.set_page_config(page_title="NYC Taxi Analytics", layout="wide")

# Sidebar navigation
st.sidebar.title("📊 Menu")
page = st.sidebar.radio(
    "Go to",
    [
        "Overview",
        "Daily Trends",
        "Customer Behavior",
        "Geography",
        "Performance Insights",
    ],
)

# Utility aggregates reused across sections
# Total revenue and trips across the month
total_revenue_all = float(daily_revenue["total_revenue"].sum()) if not daily_revenue.empty else 0.0
total_trips_all   = int(daily_revenue["trips"].sum()) if not daily_revenue.empty else 0

# -----------------------------------------------------------------------------
# PAGE: OVERVIEW
# -----------------------------------------------------------------------------
if page == "Overview":
    st.title("NYC Taxi Analytics – December 2024")

    # 1) Prominent headline: Total Revenue (on its own line)
    st.markdown("### 💵 Total Revenue (Dec 2024)")
    st.markdown(f"<h2 style='margin-top:-10px;'>${total_revenue_all:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # 2) Evenly spaced KPI cards (single row)
    #    Using exactly 5 columns to keep spacing consistent across screen sizes.
    avg_fare_all      = float(daily_revenue["avg_fare"].mean()) if not daily_revenue.empty else 0.0
    avg_distance_all  = float(daily_revenue["avg_distance"].mean()) if not daily_revenue.empty else 0.0
    avg_tip_pct_all   = float(daily_revenue["avg_tip_pct"].mean()) if not daily_revenue.empty else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Trips", f"{total_trips_all:,}")
    # Deliberately not duplicating total revenue here since it’s already headlined above
    c2.metric("Avg Fare", f"${avg_fare_all:,.2f}")
    c3.metric("Avg Distance", f"{avg_distance_all:.2f} mi")
    c4.metric("Avg Tip %", f"{avg_tip_pct_all:.2f}%")

    # Payment share (derived from payment_summary)
    if not payment_summary.empty:
        total_rev_ps = float(payment_summary["revenue"].sum())
        share = payment_summary.copy()
        share["rev_share_pct"] = (share["revenue"] / total_rev_ps * 100.0).round(2) if total_rev_ps > 0 else 0.0
        # Largest payment type share
        top_method_row = share.sort_values("rev_share_pct", ascending=False).head(1)
        if not top_method_row.empty:
            top_method = str(top_method_row["payment_type"].iloc[0])
            top_share  = float(top_method_row["rev_share_pct"].iloc[0])
            c5.metric("Top Payment Method", f"{top_method} ({top_share:.1f}%)")
        else:
            c5.metric("Top Payment Method", "N/A")
    else:
        c5.metric("Top Payment Method", "N/A")

    st.markdown("---")

    # 3) Narrative summary with concrete, interpretable statements
    #    Pulling simple facts from the data to produce clear takeaways.
    # Peak revenue day
    peak_rev_text = "N/A"
    if not daily_revenue.empty:
        peak_day = daily_revenue.sort_values("total_revenue", ascending=False).head(1)
        if not peak_day.empty:
            peak_rev_text = f"{pd.to_datetime(peak_day['trip_date'].iloc[0]).date()} (${float(peak_day['total_revenue'].iloc[0]):,.2f})"

    # Peak trip day
    peak_trips_text = "N/A"
    if not daily_revenue.empty:
        peak_trips_day = daily_revenue.sort_values("trips", ascending=False).head(1)
        if not peak_trips_day.empty:
            peak_trips_text = f"{pd.to_datetime(peak_trips_day['trip_date'].iloc[0]).date()} ({int(peak_trips_day['trips'].iloc[0]):,} trips)"

    # Peak hour (by trips)
    peak_hour_text = "N/A"
    if not hourly_trends.empty:
        peak_hour = hourly_trends.sort_values("trips", ascending=False).head(1)
        if not peak_hour.empty:
            peak_hour_text = f"{int(peak_hour['hour_of_day'].iloc[0]):02d}:00 ({int(peak_hour['trips'].iloc[0]):,} trips)"

    # Top pickup/dropoff zones (by revenue)
    top_pickup_text = "N/A"
    if not pickup_summary.empty:
        tp = pickup_summary.sort_values("revenue", ascending=False).head(1)
        if not tp.empty:
            top_pickup_text = f"{tp['pickup_zone'].iloc[0]} (${float(tp['revenue'].iloc[0]):,.2f})"
    top_dropoff_text = "N/A"
    if not dropoff_summary.empty:
        td = dropoff_summary.sort_values("revenue", ascending=False).head(1)
        if not td.empty:
            top_dropoff_text = f"{td['dropoff_zone'].iloc[0]} (${float(td['revenue'].iloc[0]):,.2f})"

    st.subheader("Executive Commentary")
    st.write(
        f"""
- **Peak revenue day:** {peak_rev_text}  
- **Peak trip day:** {peak_trips_text}  
- **Busiest hour (by trips):** {peak_hour_text}  
- **Top pickup zone (by revenue):** {top_pickup_text}  
- **Top dropoff zone (by revenue):** {top_dropoff_text}  

**Interpretation:** December shows strong holiday dynamics. Daily revenue and volume peak around late-December dates,  
with evenings driving the most trips. Payment behavior is dominated by electronic methods, and high-revenue zones are  
concentrated around airports and high-density Manhattan areas. Average fare and distance indicate that most rides are  
short-to-medium, while a stable tip percentage suggests consistent rider behavior across the month.
"""
    )

# -----------------------------------------------------------------------------
# PAGE: DAILY TRENDS
# -----------------------------------------------------------------------------
elif page == "Daily Trends":
    st.title("Daily Trends")

    # Daily revenue trend
    fig_rev = px.line(
        daily_revenue.sort_values("trip_date"),
        x="trip_date",
        y="total_revenue",
        title="Daily Total Revenue",
        markers=True,
    )
    st.plotly_chart(fig_rev, use_container_width=True)

    # Daily trips trend
    fig_trips = px.line(
        daily_revenue.sort_values("trip_date"),
        x="trip_date",
        y="trips",
        title="Daily Trips",
        markers=True,
    )
    st.plotly_chart(fig_trips, use_container_width=True)

    # Combo: trips (bars) with revenue (line)
    dr_sorted = daily_revenue.sort_values("trip_date")
    fig_combo = px.bar(
        dr_sorted,
        x="trip_date",
        y="trips",
        title="Trips vs Revenue (Overlay)",
    )
    fig_combo.add_scatter(
        x=dr_sorted["trip_date"],
        y=dr_sorted["total_revenue"],
        name="Revenue",
        mode="lines+markers",
        yaxis="y2",
    )
    # Secondary axis styling via layout update
    fig_combo.update_layout(
        yaxis=dict(title="Trips"),
        yaxis2=dict(title="Revenue", overlaying="y", side="right"),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_combo, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE: CUSTOMER BEHAVIOR
# -----------------------------------------------------------------------------
elif page == "Customer Behavior":
    st.title("Customer Behavior")

    # Payment type revenue share
    fig_payment = px.pie(
        payment_summary.sort_values("revenue", ascending=False),
        names="payment_type",
        values="revenue",
        title="Revenue Share by Payment Type",
        hole=0.3,
    )
    st.plotly_chart(fig_payment, use_container_width=True)

    # Passenger count distribution
    fig_passengers = px.bar(
        passenger_summary.sort_values("passenger_count"),
        x="passenger_count",
        y="trips",
        title="Trips by Passenger Count",
    )
    st.plotly_chart(fig_passengers, use_container_width=True)

    # Trip length buckets
    fig_length = px.bar(
        trip_length_summary.sort_values("trips", ascending=False),
        x="trip_bucket",
        y="trips",
        title="Trip Length Distribution",
        category_orders={
            "trip_bucket": [
                "Short (<2mi)",
                "Medium (2–10mi)",
                "Long (10–30mi)",
                "Very Long (>30mi)",
            ]
        },
    )
    st.plotly_chart(fig_length, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE: GEOGRAPHY
# -----------------------------------------------------------------------------
elif page == "Geography":
    st.title("Geography of Rides")

    # Top pickup zones by revenue (Top 10)
    top_pickups = pickup_summary.sort_values("revenue", ascending=False).head(10)
    fig_pickups = px.bar(
        top_pickups,
        x="pickup_zone",
        y="revenue",
        title="Top 10 Pickup Zones by Revenue",
    )
    fig_pickups.update_layout(xaxis_tickangle=-20)
    st.plotly_chart(fig_pickups, use_container_width=True)

    # Top dropoff zones by revenue (Top 10)
    top_dropoffs = dropoff_summary.sort_values("revenue", ascending=False).head(10)
    fig_dropoffs = px.bar(
        top_dropoffs,
        x="dropoff_zone",
        y="revenue",
        title="Top 10 Dropoff Zones by Revenue",
    )
    fig_dropoffs.update_layout(xaxis_tickangle=-20)
    st.plotly_chart(fig_dropoffs, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE: PERFORMANCE INSIGHTS (replaces "Outliers")
# -----------------------------------------------------------------------------
elif page == "Performance Insights":
    st.title("Performance Insights")

    # 1) Peak days (top 5 by revenue and by trips)
    left, right = st.columns(2)
    with left:
        st.subheader("Top 5 Days by Revenue")
        top_days_rev = (
            daily_revenue.sort_values("total_revenue", ascending=False)
            .head(5)[["trip_date", "total_revenue", "trips", "avg_fare", "avg_tip_pct"]]
        )
        st.dataframe(top_days_rev, use_container_width=True)
    with right:
        st.subheader("Top 5 Days by Trips")
        top_days_trips = (
            daily_revenue.sort_values("trips", ascending=False)
            .head(5)[["trip_date", "trips", "total_revenue", "avg_fare", "avg_tip_pct"]]
        )
        st.dataframe(top_days_trips, use_container_width=True)

    st.markdown("---")

    # 2) Peak hours (by trips)
    st.subheader("Peak Hours by Trips")
    top_hours = hourly_trends.sort_values("trips", ascending=False).head(8)
    fig_hours = px.bar(
        top_hours.sort_values("hour_of_day"),
        x="hour_of_day",
        y="trips",
        title="Top Hours (Trips)",
    )
    st.plotly_chart(fig_hours, use_container_width=True)

    # 3) Zone leaderboards (Top N parameter)
    st.markdown("---")
    st.subheader("Zone Leaderboards")
    top_n = st.slider("Top N rows", min_value=5, max_value=25, value=10, step=1)

    zcol1, zcol2 = st.columns(2)
    with zcol1:
        st.write("Top Pickup Zones (by revenue)")
        st.dataframe(
            pickup_summary.sort_values("revenue", ascending=False)
            .head(top_n)[["pickup_zone", "trips", "revenue", "avg_fare"]],
            use_container_width=True,
        )
    with zcol2:
        st.write("Top Dropoff Zones (by revenue)")
        st.dataframe(
            dropoff_summary.sort_values("revenue", ascending=False)
            .head(top_n)[["dropoff_zone", "trips", "revenue", "avg_fare"]],
            use_container_width=True,
        )

    st.markdown("---")

    # 4) Efficiency metric: Revenue per Trip over time (derived from daily_revenue)
    st.subheader("Revenue per Trip Over Time")
    if total_trips_all > 0:
        dr_eff = daily_revenue.copy()
        dr_eff["revenue_per_trip"] = (dr_eff["total_revenue"] / dr_eff["trips"]).round(2)
        fig_rpt = px.line(
            dr_eff.sort_values("trip_date"),
            x="trip_date",
            y="revenue_per_trip",
            title="Revenue per Trip (Daily)",
            markers=True,
        )
        st.plotly_chart(fig_rpt, use_container_width=True)
    else:
        st.info("No trips available to compute Revenue per Trip.")
