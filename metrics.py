from typing import Any, Dict, Optional
import pandas as pd


def get_kpi_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Filters to delivered orders. Computes, on the ORDER level
    (not line-item level -- group by order_id first, summing
    price per order, before averaging):
      - total_revenue: sum of price across all line items
      - total_orders: count of distinct order_id
      - avg_order_value: total_revenue / total_orders
    Returns a dict with keys: total_revenue, total_orders, avg_order_value.
    Do not attempt MoM/YoY here -- that's out of scope for this
    function since it needs a comparison period; leave as a
    static snapshot of whatever df is passed in.
    """
    delivered = df[df["order_status"] == "delivered"]
    if delivered.empty:
        return {
            "total_revenue": 0.0,
            "total_orders": 0,
            "avg_order_value": 0.0,
        }

    order_totals = delivered.groupby("order_id")["price"].sum()
    total_revenue = float(order_totals.sum())
    total_orders = int(len(order_totals))
    avg_order_value = float(order_totals.mean()) if total_orders > 0 else 0.0

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "avg_order_value": avg_order_value,
    }


def get_revenue_trend(df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """
    Filters to delivered orders. Groups order_purchase_timestamp
    by the given frequency (default monthly, 'M') and sums price.
    Returns a DataFrame with two columns: period (Timestamp) and
    revenue (float), sorted chronologically. freq should also
    accept 'W' (weekly) and 'D' (daily) since the dashboard may
    want to toggle granularity later.
    """
    delivered = df[df["order_status"] == "delivered"]
    if delivered.empty:
        return pd.DataFrame(
            {
                "period": pd.Series(dtype="datetime64[ns]"),
                "revenue": pd.Series(dtype="float64"),
            }
        )

    # Normalize frequency for pandas compatibility (in pandas 3.0+, 'M' offset is replaced by 'ME')
    freq_norm = freq.strip()
    if freq_norm.upper() == "M":
        pandas_freq = "ME"
    elif freq_norm.upper() == "W":
        pandas_freq = "W"
    elif freq_norm.upper() == "D":
        pandas_freq = "D"
    else:
        pandas_freq = freq_norm

    trend = (
        delivered.groupby(pd.Grouper(key="order_purchase_timestamp", freq=pandas_freq))["price"]
        .sum()
        .reset_index()
    )
    trend.columns = ["period", "revenue"]
    trend["revenue"] = trend["revenue"].astype(float)
    trend = trend.sort_values("period").reset_index(drop=True)
    return trend


def get_top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Filters to delivered orders. Groups by
    product_category_name_english, summing price and counting
    distinct order_id (as order_count). Returns top n rows sorted
    by summed price descending. Columns: product_category_name_english,
    revenue, order_count.
    """
    delivered = df[df["order_status"] == "delivered"]
    if delivered.empty:
        return pd.DataFrame(
            {
                "product_category_name_english": pd.Series(dtype="str"),
                "revenue": pd.Series(dtype="float64"),
                "order_count": pd.Series(dtype="int64"),
            }
        )

    top = (
        delivered.groupby("product_category_name_english")
        .agg(revenue=("price", "sum"), order_count=("order_id", "nunique"))
        .reset_index()
        .sort_values(by="revenue", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )
    top["revenue"] = top["revenue"].astype(float)
    top["order_count"] = top["order_count"].astype(int)
    return top[["product_category_name_english", "revenue", "order_count"]]


def get_regional_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters to delivered orders. Groups by customer_state, summing
    price and counting distinct order_id. Returns all states sorted
    by revenue descending. Columns: customer_state, revenue, order_count.
    """
    delivered = df[df["order_status"] == "delivered"]
    if delivered.empty:
        return pd.DataFrame(
            {
                "customer_state": pd.Series(dtype="str"),
                "revenue": pd.Series(dtype="float64"),
                "order_count": pd.Series(dtype="int64"),
            }
        )

    breakdown = (
        delivered.groupby("customer_state")
        .agg(revenue=("price", "sum"), order_count=("order_id", "nunique"))
        .reset_index()
        .sort_values(by="revenue", ascending=False)
        .reset_index(drop=True)
    )
    breakdown["revenue"] = breakdown["revenue"].astype(float)
    breakdown["order_count"] = breakdown["order_count"].astype(int)
    return breakdown[["customer_state", "revenue", "order_count"]]


def get_customer_segments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters to delivered orders. Groups by customer_unique_id
    (NOT customer_id) and counts distinct order_id per customer.
    Classifies each customer as 'repeat' (2+ distinct orders) or
    'one-time' (1 order). Returns a DataFrame with columns:
    segment ('repeat' / 'one-time'), customer_count, and
    revenue (total price attributable to that segment).
    """
    delivered = df[df["order_status"] == "delivered"]
    if delivered.empty:
        return pd.DataFrame(
            {
                "segment": ["repeat", "one-time"],
                "customer_count": [0, 0],
                "revenue": [0.0, 0.0],
            }
        )

    # Group by real-world customer identifier
    cust_agg = delivered.groupby("customer_unique_id").agg(
        order_count=("order_id", "nunique"),
        revenue=("price", "sum"),
    )
    cust_agg["segment"] = cust_agg["order_count"].apply(
        lambda count: "repeat" if count >= 2 else "one-time"
    )

    segment_df = (
        cust_agg.groupby("segment")
        .agg(
            customer_count=("revenue", "count"),
            revenue=("revenue", "sum"),
        )
        .reset_index()
    )

    # Ensure both segments exist in deterministic order
    all_segments = pd.DataFrame({"segment": ["repeat", "one-time"]})
    result = all_segments.merge(segment_df, on="segment", how="left").fillna(
        {"customer_count": 0, "revenue": 0.0}
    )
    result["customer_count"] = result["customer_count"].astype(int)
    result["revenue"] = result["revenue"].astype(float)

    return result[["segment", "customer_count", "revenue"]]
