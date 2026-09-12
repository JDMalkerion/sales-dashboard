import datetime
from pathlib import Path
from typing import Any, Optional, Sequence, Union
import pandas as pd


def load_data(data_dir: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Loads and joins all Olist CSVs into one flat DataFrame,
    one row per order item, per the join plan:
    Base table: order_items
    1. Join orders on order_id -> order_status, order_purchase_timestamp,
       order_delivered_customer_date, order_estimated_delivery_date, customer_id
    2. Join customers on customer_id (via orders) -> customer_state, customer_city
    3. Join products on product_id -> product_category_name
    4. Join product_category_name_translation on product_category_name -> product_category_name_english

    Returns the cleaned, joined table, not yet filtered by
    order status (that's left as a column: order_status).
    """
    if data_dir is not None:
        base_path = Path(data_dir)
    else:
        # Check current working directory first, then file parent directory
        if Path("data").exists():
            base_path = Path("data")
        else:
            base_path = Path(__file__).resolve().parent / "data"

    # 1. Load CSV datasets
    order_items = pd.read_csv(base_path / "olist_order_items_dataset.csv")
    orders = pd.read_csv(base_path / "olist_orders_dataset.csv")
    customers = pd.read_csv(base_path / "olist_customers_dataset.csv")
    products = pd.read_csv(base_path / "olist_products_dataset.csv")
    category_trans = pd.read_csv(base_path / "product_category_name_translation.csv")

    # 2. Join orders onto order_items (base table)
    orders_cols = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    df = order_items.merge(orders[orders_cols], on="order_id", how="left")

    # 3. Join customers on customer_id (via orders)
    customer_cols = [
        "customer_id",
        "customer_unique_id",
        "customer_state",
        "customer_city",
    ]
    df = df.merge(customers[customer_cols], on="customer_id", how="left")

    # 4. Join products on product_id
    product_cols = ["product_id", "product_category_name"]
    df = df.merge(products[product_cols], on="product_id", how="left")

    # 5. Join translation on product_category_name
    df = df.merge(category_trans, on="product_category_name", how="left")

    # Cleaning step 1: Parse to datetime
    date_cols = [
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Cleaning step 2: Keep order_status as column (retained, no filter applied)

    # Cleaning step 3: Map product_category_name to English, fill unmapped or missing with "unknown"
    df["product_category_name_english"] = df["product_category_name_english"].fillna("unknown")

    # Cleaning step 4: Drop rows with a null customer_state (print count dropped)
    null_state_count = int(df["customer_state"].isna().sum())
    print(f"Dropped {null_state_count} rows with null customer_state")
    if null_state_count > 0:
        df = df.dropna(subset=["customer_state"]).reset_index(drop=True)

    return df


def filter_data(
    df: pd.DataFrame,
    date_range: Optional[Union[Sequence[Any], Any]] = None,
    state: Optional[Union[str, Sequence[str]]] = None,
    category: Optional[Union[str, Sequence[str]]] = None,
) -> pd.DataFrame:
    """
    Filters df to rows where order_purchase_timestamp falls
    within date_range (inclusive). Optionally filters on
    customer_state and product_category_name_english.
    None (or 'All') for state/category means no filter on
    that dimension.
    """
    filtered_df = df.copy()

    # 1. Filter by date_range
    if date_range is not None and date_range != "All":
        start_val = None
        end_val = None

        if isinstance(date_range, (list, tuple)):
            if len(date_range) >= 2:
                start_val, end_val = date_range[0], date_range[1]
            elif len(date_range) == 1:
                start_val = date_range[0]
        else:
            start_val, end_val = date_range, date_range

        if start_val is not None:
            start_ts = pd.to_datetime(start_val)
            filtered_df = filtered_df[filtered_df["order_purchase_timestamp"] >= start_ts]

        if end_val is not None:
            end_ts = pd.to_datetime(end_val)
            # If end_val has no explicit time component (e.g. date object or YYYY-MM-DD string),
            # expand to end of that day so filtering is fully inclusive.
            if (
                (isinstance(end_val, datetime.date) and not isinstance(end_val, datetime.datetime))
                or (isinstance(end_val, str) and len(end_val.strip()) <= 10)
                or (isinstance(end_val, pd.Timestamp) and end_ts.time() == datetime.time(0, 0, 0))
            ):
                end_ts = end_ts + pd.Timedelta(days=1) - pd.Timedelta("1ns")

            filtered_df = filtered_df[filtered_df["order_purchase_timestamp"] <= end_ts]

    # 2. Filter by customer_state
    if state is not None and state != "All":
        if isinstance(state, (list, tuple, set)):
            valid_states = [s for s in state if s != "All"]
            if valid_states:
                filtered_df = filtered_df[filtered_df["customer_state"].isin(valid_states)]
        else:
            filtered_df = filtered_df[filtered_df["customer_state"] == state]

    # 3. Filter by product_category_name_english
    if category is not None and category != "All":
        if isinstance(category, (list, tuple, set)):
            valid_categories = [c for c in category if c != "All"]
            if valid_categories:
                filtered_df = filtered_df[
                    filtered_df["product_category_name_english"].isin(valid_categories)
                ]
        else:
            filtered_df = filtered_df[filtered_df["product_category_name_english"] == category]

    return filtered_df
