import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
import plotly.express as px

# ----------------------------------------------------------------------------
# DATABASE CONNECTION
# ----------------------------------------------------------------------------
# Pull connection string from Streamlit Cloud secrets.
# Locally, you can set an env variable or hardcode for testing.
DB_URL = os.getenv("DATABASE_URL")

# Create engine for querying Supabase Postgres (via pooler endpoint)
engine = create_engine(DB_URL)

# ----------------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------------
@st.cache_data
def load_table(table_name):
    """
    Load a table or materialized view from the database into a Pandas DataFrame.
    Cached for speed so the app isn't re-querying on every interaction.
    """
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)

# Preload all summary tables
daily_revenue = load_table("daily_revenue")
payment_summary = load_table("payment_summary")
passenger_summary = load_table("passenger_summary")
pickup_summary = load_table("pickup_summary")
dropoff_summary = load_table("dropoff_summary")
hourly_trends = load_table("hourly_trends")
trip_length_summary = load_table("trip_length_summary")
outliers = load_table("outliers")

# ----------------------------------------------------------------------------
# STREAMLIT PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(page_title="NYC Taxi Analytics", layout="wide")

# Sidebar navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Executive Summary",
        "Daily Trends",
        "Customer Behavior",
        "Geography",
        "Outliers"
    ]
)

# ----------------------------------------------------------------------------
# PAGE 1: EXECUTIVE SUMMARY
# ----------------------------------------------------------------------------
if page == "Executive Summary":
    st.title("🚖 NYC Taxi Analytics – December 2024")

    # KPI cards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total Trips", f"{daily_revenue['trips'].sum():,}")
    kpi2.metric("Total Revenue", f"${daily_revenue['total_revenue'].sum():,.2f}")
    kpi3.metric("Avg Fare", f"${daily_revenue['avg_fare'].mean():.2f}")
    kpi4.metric("Avg Distance", f"{daily_revenue['avg_distance'].mean():.2f} mi")
    kpi5.metric("Avg Tip %", f"{daily_revenue['avg_tip_pct'].mean():.2f}%")

    st.markdown("---")
    st.subheader("Key Insights")
    st.write("""
    - **Trips peaked** around Christmas and New Year’s Eve.  
    - **Credit card dominates** as the payment method (>90% of revenue).  
    - **Most rides are short to medium trips** (under 10 miles).  
    """)

# ----------------------------------------------------------------------------
# PAGE 2: DAILY TRENDS
# ----------------------------------------------------------------------------
elif page == "Daily Trends":
    st.title("📈 Daily Trends")

    # Line chart: Revenue per day
    fig_rev = px.line(
        daily_revenue,
        x="trip_date",
        y="total_revenue",
        title="Daily Total Revenue",
        markers=True
    )
    st.plotly_chart(fig_rev, use_container_width=True)

    # Line chart: Trips per day
    fig_trips = px.line(
        daily_revenue,
        x="trip_date",
        y="trips",
        title="Daily Trips Volume",
        markers=True
    )
    st.plotly_chart(fig_trips, use_container_width=True)

    # Combo-style: Trips vs Revenue
    fig_combo = px.bar(
        daily_revenue,
        x="trip_date",
        y="trips",
        title="Trips vs Revenue (Overlay)"
    )
    fig_combo.add_scatter(
        x=daily_revenue["trip_date"], 
        y=daily_revenue["total_revenue"], 
        name="Revenue", 
        mode="lines+markers"
    )
    st.plotly_chart(fig_combo, use_container_width=True)

# ----------------------------------------------------------------------------
# PAGE 3: CUSTOMER BEHAVIOR
# ----------------------------------------------------------------------------
elif page == "Customer Behavior":
    st.title("💳 Customer Behavior")

    # Pie chart: Payment type
    fig_payment = px.pie(
        payment_summary,
        names="payment_type",
        values="revenue",
        title="Revenue Share by Payment Type"
    )
    st.plotly_chart(fig_payment, use_container_width=True)

    # Bar: Passenger count
    fig_passengers = px.bar(
        passenger_summary,
        x="passenger_count",
        y="trips",
        title="Trips by Passenger Count"
    )
    st.plotly_chart(fig_passengers, use_container_width=True)

    # Bar: Trip length distribution
    fig_length = px.bar(
        trip_length_summary,
        x="trip_bucket",
        y="trips",
        title="Trip Length Distribution",
        category_orders={"trip_bucket": ["Short (<2mi)", "Medium (2–10mi)", "Long (10–30mi)", "Very Long (>30mi)"]}
    )
    st.plotly_chart(fig_length, use_container_width=True)

# ----------------------------------------------------------------------------
# PAGE 4: GEOGRAPHY
# ----------------------------------------------------------------------------
elif page == "Geography":
    st.title("📍 Geography of Rides")

    # Top 10 Pickup zones
    top_pickups = pickup_summary.sort_values("revenue", ascending=False).head(10)
    fig_pickups = px.bar(
        top_pickups,
        x="pickup_zone",
        y="revenue",
        title="Top 10 Pickup Zones by Revenue"
    )
    st.plotly_chart(fig_pickups, use_container_width=True)

    # Top 10 Dropoff zones
    top_dropoffs = dropoff_summary.sort_values("revenue", ascending=False).head(10)
    fig_dropoffs = px.bar(
        top_dropoffs,
        x="dropoff_zone",
        y="revenue",
        title="Top 10 Dropoff Zones by Revenue"
    )
    st.plotly_chart(fig_dropoffs, use_container_width=True)

    # Map: Pickup revenue heatmap
    st.subheader("🗺️ Revenue by Pickup Zone (Map)")

    # Join pickup_summary with taxi_zones to get lat/lon
    pickup_geo = pickup_summary.merge(
        load_table("taxi_zones")[["LocationID", "Zone", "lat", "lon"]],
        left_on="pickup_zone",
        right_on="Zone",
        how="left"
    )

    # Create map layer
    import pydeck as pdk
    pickup_layer = pdk.Layer(
        "ScatterplotLayer",
        data=pickup_geo,
        get_position="[lon, lat]",
        get_radius="revenue / 100",  # Scale bubbles by revenue
        get_fill_color="[255, 140, 0, 160]",  # orange bubbles
        pickable=True,
    )

    view_state = pdk.ViewState(latitude=40.7128, longitude=-74.0060, zoom=10)

    st.pydeck_chart(pdk.Deck(layers=[pickup_layer], initial_view_state=view_state, tooltip={"text": "{pickup_zone}\nRevenue: ${revenue}"}))

# ----------------------------------------------------------------------------
# PAGE 5: OUTLIERS
# ----------------------------------------------------------------------------
elif page == "Outliers":
    st.title("⚠️ Outlier Rides")

    st.write("These are unusual trips with extreme distances, fares, or passenger counts.")
    st.dataframe(outliers.head(50), use_container_width=True)
