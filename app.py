import datetime
from typing import Optional, Tuple
import pandas as pd
import plotly.express as px
import streamlit as st

import data_loader
import metrics

# 1. Page Configuration
st.set_page_config(
    layout="wide",
    page_title="Sales Dashboard",
    page_icon="📊",
)

# Custom CSS for polished aesthetics
st.markdown(
    """
    <style>
    /* Metric card enhancements */
    [data-testid="stMetric"] {
        background-color: rgba(240, 242, 246, 0.5);
        border: 1px solid rgba(0, 0, 0, 0.08);
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    @media (prefers-color-scheme: dark) {
        [data-testid="stMetric"] {
            background-color: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    }
    .main-title {
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748b;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 2. Title and Description
st.title("📊 Brazilian E-Commerce Sales Dashboard")
st.markdown(
    """
    An interactive executive analytics dashboard exploring orders, revenue trajectories, regional performance,
    and customer repeat patterns across Brazil from the **Olist Brazilian E-Commerce dataset**.
    """
)


# 3. Cached Data Loading
@st.cache_data(show_spinner="Loading and preparing Olist dataset...")
def get_cached_data() -> pd.DataFrame:
    """Loads and caches the flattened Olist dataset."""
    return data_loader.load_data()


raw_df = get_cached_data()

# 4. Dynamic Sidebar Filters
st.sidebar.header("🔍 Filter Dashboard")

# Date range bounds from dataset
min_purchase_date = raw_df["order_purchase_timestamp"].min().date()
max_purchase_date = raw_df["order_purchase_timestamp"].max().date()

selected_date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_purchase_date, max_purchase_date),
    min_value=min_purchase_date,
    max_value=max_purchase_date,
    help="Filter by order purchase timestamp range (inclusive).",
)

# Handle intermediate selection state where only one date is picked
date_range_filter: Optional[Tuple[datetime.date, datetime.date]] = None
if isinstance(selected_date_range, (list, tuple)):
    if len(selected_date_range) == 2:
        date_range_filter = (selected_date_range[0], selected_date_range[1])
    elif len(selected_date_range) == 1:
        date_range_filter = (selected_date_range[0], selected_date_range[0])
elif isinstance(selected_date_range, datetime.date):
    date_range_filter = (selected_date_range, selected_date_range)

# Dynamic Region Dropdown
unique_states = sorted(raw_df["customer_state"].dropna().unique().tolist())
selected_state = st.sidebar.selectbox(
    "Region (Customer State)",
    options=["All"] + unique_states,
    index=0,
    help="Filter orders by customer state.",
)

# Dynamic Category Dropdown
unique_categories = sorted(raw_df["product_category_name_english"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox(
    "Product Category",
    options=["All"] + unique_categories,
    index=0,
    help="Filter orders by English product category name.",
)

# 5. Apply Filtering
state_param = None if selected_state == "All" else selected_state
category_param = None if selected_category == "All" else selected_category

filtered_df = data_loader.filter_data(
    raw_df,
    date_range=date_range_filter,
    state=state_param,
    category=category_param,
)

# 9. Handle Empty-Filter Edge Case
delivered_orders_count = (filtered_df["order_status"] == "delivered").sum()

if delivered_orders_count == 0:
    st.warning("No data available for the selected filters.")
else:
    # 6. KPI Summary Row
    kpi = metrics.get_kpi_summary(filtered_df)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Total Revenue",
            value=f"R$ {kpi['total_revenue']:,.2f}",
        )
    with col2:
        st.metric(
            label="Total Orders",
            value=f"{kpi['total_orders']:,}",
        )
    with col3:
        st.metric(
            label="Avg Order Value",
            value=f"R$ {kpi['avg_order_value']:,.2f}",
        )

    st.markdown("---")

    # 7. First Row of Charts (Revenue Trend & Top 10 Products)
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("📈 Monthly Revenue Trend")
        trend_df = metrics.get_revenue_trend(filtered_df, freq="M")
        fig_trend = px.line(
            trend_df,
            x="period",
            y="revenue",
            markers=True,
            labels={"period": "Month", "revenue": "Revenue (R$)"},
        )
        fig_trend.update_traces(
            line_color="#2563eb",
            marker=dict(size=6, color="#1d4ed8"),
            hovertemplate="<b>Date</b>: %{x|%b %Y}<br><b>Revenue</b>: R$ %{y:,.2f}<extra></extra>",
        )
        fig_trend.update_layout(
            margin=dict(l=20, r=20, t=30, b=20),
            hovermode="x unified",
            xaxis=dict(showgrid=True, gridcolor="rgba(150, 150, 150, 0.15)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(150, 150, 150, 0.15)"),
        )
        st.plotly_chart(fig_trend)

    with row1_col2:
        st.subheader("🏆 Top 10 Product Categories")
        top_products = metrics.get_top_products(filtered_df, n=10)
        fig_top = px.bar(
            top_products,
            x="revenue",
            y="product_category_name_english",
            orientation="h",
            labels={
                "revenue": "Revenue (R$)",
                "product_category_name_english": "Category",
                "order_count": "Orders",
            },
            custom_data=["order_count"],
        )
        fig_top.update_traces(
            marker_color="#0d9488",
            hovertemplate="<b>%{y}</b><br><b>Revenue</b>: R$ %{x:,.2f}<br><b>Orders</b>: %{customdata[0]:,}<extra></extra>",
        )
        fig_top.update_layout(
            yaxis=dict(categoryorder="total ascending", title=""),
            xaxis=dict(showgrid=True, gridcolor="rgba(150, 150, 150, 0.15)"),
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(fig_top)

    # 8. Second Row of Charts (Regional Breakdown & Customer Segments)
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("🗺️ Revenue by Customer State")
        regional_df = metrics.get_regional_breakdown(filtered_df)
        fig_reg = px.bar(
            regional_df,
            x="customer_state",
            y="revenue",
            labels={
                "customer_state": "State",
                "revenue": "Revenue (R$)",
                "order_count": "Orders",
            },
            custom_data=["order_count"],
        )
        fig_reg.update_traces(
            marker_color="#4f46e5",
            hovertemplate="<b>State</b>: %{x}<br><b>Revenue</b>: R$ %{y:,.2f}<br><b>Orders</b>: %{customdata[0]:,}<extra></extra>",
        )
        fig_reg.update_layout(
            xaxis=dict(title="State"),
            yaxis=dict(showgrid=True, gridcolor="rgba(150, 150, 150, 0.15)"),
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(fig_reg)

    with row2_col2:
        st.subheader("👥 Customer Segments (Revenue Share)")
        segment_df = metrics.get_customer_segments(filtered_df)
        fig_seg = px.pie(
            segment_df,
            names="segment",
            values="revenue",
            hole=0.45,
            color="segment",
            color_discrete_map={
                "repeat": "#10b981",
                "one-time": "#3b82f6",
            },
            custom_data=["customer_count"],
        )
        fig_seg.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>Segment</b>: %{label}<br><b>Revenue</b>: R$ %{value:,.2f} (%{percent})<br><b>Customers</b>: %{customdata[0]:,}<extra></extra>",
        )
        fig_seg.update_layout(
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_seg)
