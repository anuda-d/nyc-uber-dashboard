# dashboard.py
# -----------------------------------------------------------------------------
# NYC Taxi Analytics – Streamlit Dashboard
# -----------------------------------------------------------------------------

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
import plotly.express as px

# -----------------------------------------------------------------------------
# Database connection
# -----------------------------------------------------------------------------
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    st.error("DATABASE_URL is not set. Please configure it in your environment or Streamlit secrets.")
    st.stop()

engine = create_engine(DB_URL)

# -----------------------------------------------------------------------------
# Data loading
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_table(table_name: str) -> pd.DataFrame:
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)

daily_revenue       = load_table("daily_revenue")
payment_summary     = load_table("payment_summary")
passenger_summary   = load_table("passenger_summary")
pickup_summary      = load_table("pickup_summary")
dropoff_summary     = load_table("dropoff_summary")
hourly_trends       = load_table("hourly_trends")
trip_length_summary = load_table("trip_length_summary")

# -----------------------------------------------------------------------------
# Global config
# -----------------------------------------------------------------------------
st.set_page_config(page_title="NYC Taxi Analytics", layout="wide")

st.sidebar.title("📊 Menu")
page = st.sidebar.radio(
    "Go to",
    [
        "Overview",
        "Daily Trends",
        "Performance Insights",
        "Customer Behavior",
        "Geography",
    ],
)

# Pre-calc aggregates
total_revenue_all = float(daily_revenue["total_revenue"].sum()) if not daily_revenue.empty else 0.0
total_trips_all   = int(daily_revenue["trips"].sum()) if not daily_revenue.empty else 0

# -----------------------------------------------------------------------------
# PAGE: EXECUTIVE OVERVIEW
# -----------------------------------------------------------------------------
if page == "Overview":
    st.title("NYC Taxi Analytics – December 2024")

    # Highlight: Total Revenue
    st.markdown("### 💵 Total Revenue (Dec 2024)")
    st.markdown(f"<h2 style='margin-top:-10px;'>${total_revenue_all:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # KPI cards
    avg_fare_all     = float(daily_revenue["avg_fare"].mean()) if not daily_revenue.empty else 0.0
    avg_distance_all = float(daily_revenue["avg_distance"].mean()) if not daily_revenue.empty else 0.0
    avg_tip_pct_all  = float(daily_revenue["avg_tip_pct"].mean()) if not daily_revenue.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Trips", f"{total_trips_all:,}")
    c2.metric("Avg Fare", f"${avg_fare_all:,.2f}")
    c3.metric("Avg Distance", f"{avg_distance_all:.2f} mi")
    c4.metric("Avg Tip %", f"{avg_tip_pct_all:.2f}%")

    # Payment share (fix to ensure labels fit)
    st.markdown("---")
    st.subheader("Top Payment Method")
    if not payment_summary.empty:
        total_rev_ps = float(payment_summary["revenue"].sum())
        if total_rev_ps > 0:
            share = payment_summary.copy()
            share["rev_share_pct"] = (share["revenue"] / total_rev_ps * 100.0).round(2)
            top_row = share.sort_values("rev_share_pct", ascending=False).head(1)
            if not top_row.empty:
                st.metric(
                    "Most Used",
                    f"{top_row['payment_type'].iloc[0]} ({top_row['rev_share_pct'].iloc[0]:.1f}%)",
                )
            else:
                st.metric("Most Used", "N/A")
    else:
        st.metric("Most Used", "N/A")

    # Executive Commentary
    st.markdown("---")
    st.subheader("Commentary")

    if not daily_revenue.empty:
        peak_day = daily_revenue.sort_values("total_revenue", ascending=False).head(1)
        peak_trips_day = daily_revenue.sort_values("trips", ascending=False).head(1)
        peak_hour = hourly_trends.sort_values("trips", ascending=False).head(1)
        top_pickup = pickup_summary.sort_values("trips", ascending=False).head(1)
        top_dropoff = dropoff_summary.sort_values("trips", ascending=False).head(1)

        st.write(
            f"""
**Key Takeaways from December 2024:**

- **Holiday Effect:** The busiest revenue day was **{pd.to_datetime(peak_day['trip_date'].iloc[0]).date()}**, 
  reflecting the holiday and year-end surge, with over **${float(peak_day['total_revenue'].iloc[0]):,.2f}** generated.
- **Volume vs. Value:** The day with the most trips, **{pd.to_datetime(peak_trips_day['trip_date'].iloc[0]).date()}**, 
  did not coincide with the peak revenue day — highlighting how *short, frequent rides don’t always translate to higher earnings*. 
- **Peak Travel Hour:** The busiest time was around **{int(peak_hour['hour_of_day'].iloc[0]):02d}:00**, when NYC commuters and nightlife overlap.  
- **Geographic Insights:** The leading pickup zone was **{top_pickup['pickup_zone'].iloc[0]}**, 
  while the top dropoff was **{top_dropoff['dropoff_zone'].iloc[0]}** — reinforcing that airports and Manhattan remain economic anchors.  

**Interpretation:** The December dataset illustrates how seasonality, urban mobility, and economic patterns intersect.  
Electronic payments dominate, suggesting a nearly cashless taxi economy. Revenue concentration in a few zones indicates both opportunity (serving high-demand hubs) and vulnerability (dependence on airports/tourist flows).  
For operators, balancing fleet deployment across these dynamics could unlock efficiency gains.  
"""
        )
    else:
        st.info("No data available for commentary.")

# -----------------------------------------------------------------------------
# PAGE: DAILY TRENDS
# -----------------------------------------------------------------------------
elif page == "Daily Trends":
    st.title("Daily Trends")

    fig_rev = px.line(
        daily_revenue.sort_values("trip_date"),
        x="trip_date",
        y="total_revenue",
        title="Daily Total Revenue",
        markers=True,
    )
    st.plotly_chart(fig_rev, use_container_width=True)

    fig_trips = px.line(
        daily_revenue.sort_values("trip_date"),
        x="trip_date",
        y="trips",
        title="Daily Trips",
        markers=True,
    )
    st.plotly_chart(fig_trips, use_container_width=True)

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
    fig_combo.update_layout(
        yaxis=dict(title="Trips"),
        yaxis2=dict(title="Revenue", overlaying="y", side="right"),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_combo, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE: PERFORMANCE INSIGHTS
# -----------------------------------------------------------------------------
elif page == "Performance Insights":
    st.title("Performance Insights")

    # Top 5 days
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 5 Days by Revenue")
        st.dataframe(
            daily_revenue.sort_values("total_revenue", ascending=False)
            .head(5)[["trip_date", "total_revenue", "trips", "avg_fare", "avg_tip_pct"]],
            use_container_width=True,
        )
    with c2:
        st.subheader("Top 5 Days by Trips")
        st.dataframe(
            daily_revenue.sort_values("trips", ascending=False)
            .head(5)[["trip_date", "trips", "total_revenue", "avg_fare", "avg_tip_pct"]],
            use_container_width=True,
        )

    st.markdown("---")
    st.subheader("Peak Hours")
    top_hours = hourly_trends.sort_values("trips", ascending=False).head(8)
    fig_hours = px.bar(
        top_hours.sort_values("hour_of_day"),
        x="hour_of_day",
        y="trips",
        title="Top Hours by Trips",
    )
    st.plotly_chart(fig_hours, use_container_width=True)

    st.markdown("---")
    st.subheader("Zone Leaderboards")
    top_n = st.slider("Top N rows", 5, 25, 10, step=1)

    z1, z2 = st.columns(2)
    with z1:
        st.write("Top Pickup Zones (by Trips)")
        st.dataframe(
            pickup_summary.sort_values("trips", ascending=False)
            .head(top_n)[["pickup_zone", "trips", "revenue", "avg_fare"]],
            use_container_width=True,
        )
    with z2:
        st.write("Top Dropoff Zones (by Trips)")
        st.dataframe(
            dropoff_summary.sort_values("trips", ascending=False)
            .head(top_n)[["dropoff_zone", "trips", "revenue", "avg_fare"]],
            use_container_width=True,
        )

    st.markdown("---")
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
        st.info("No trips available.")

# -----------------------------------------------------------------------------
# PAGE: CUSTOMER BEHAVIOR
# -----------------------------------------------------------------------------
elif page == "Customer Behavior":
    st.title("Customer Behavior")

    fig_payment = px.pie(
        payment_summary.sort_values("revenue", ascending=False),
        names="payment_type",
        values="revenue",
        title="Revenue Share by Payment Type",
        hole=0.3,
    )
    st.plotly_chart(fig_payment, use_container_width=True)

    fig_passengers = px.bar(
        passenger_summary.sort_values("passenger_count"),
        x="passenger_count",
        y="trips",
        title="Trips by Passenger Count",
    )
    st.plotly_chart(fig_passengers, use_container_width=True)

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

    top_pickups = pickup_summary.sort_values("trips", ascending=False).head(10)
    fig_pickups = px.bar(
        top_pickups,
        x="pickup_zone",
        y="trips",
        title="Top 10 Pickup Zones by Trips",
    )
    fig_pickups.update_layout(xaxis_tickangle=-20)
    st.plotly_chart(fig_pickups, use_container_width=True)

    top_dropoffs = dropoff_summary.sort_values("trips", ascending=False).head(10)
    fig_dropoffs = px.bar(
        top_dropoffs,
        x="dropoff_zone",
        y="trips",
        title="Top 10 Dropoff Zones by Trips",
    )
    fig_dropoffs.update_layout(xaxis_tickangle=-20)
    st.plotly_chart(fig_dropoffs, use_container_width=True)
