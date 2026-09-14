# Brazilian E-Commerce Sales Dashboard

An interactive Streamlit dashboard analyzing revenue trends, regional performance, top product categories, and customer retention using real-world marketplace data.

---

## Business Context & Use Case

This dashboard is designed to answer the fundamental operational and strategic questions an e-commerce merchant or marketplace operator faces:

- Where is revenue coming from, and how is it trending over time?
- Which product categories and geographic regions generate the highest sales volume?
- How much of total revenue depends on repeat customers versus one-time buyers?

By scoping line items to delivered orders and providing dynamic filters across date ranges, customer states, and product categories, the dashboard provides a clear, interactive view of store performance without requiring SQL queries or raw spreadsheet wrangling.

---

## Tech Stack

- Python
- Streamlit
- Pandas
- Plotly

---

## How to Run Locally

Follow these steps in order to set up and run the dashboard locally:

```bash
git clone <repo-url>
cd sales-dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dataset Setup

The raw Olist dataset files are gitignored due to file size. Download the dataset directly from Kaggle:

1. Download the [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
2. Extract the 9 CSV files into the `data/` directory at the project root:
   - `olist_orders_dataset.csv`
   - `olist_order_items_dataset.csv`
   - `olist_order_payments_dataset.csv`
   - `olist_order_reviews_dataset.csv`
   - `olist_customers_dataset.csv`
   - `olist_products_dataset.csv`
   - `olist_sellers_dataset.csv`
   - `olist_geolocation_dataset.csv`
   - `product_category_name_translation.csv`

### Launch App

Once dependencies are installed and the CSVs are placed in `data/`, start the application:

```bash
streamlit run app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`.

---

## Key Insights

Based on the verified analysis of delivered orders across the full dataset:

- **Volume & Revenue Baseline**: Generated **R$ 13.2M** in total revenue across **96,478** delivered orders, with an average order value (AOV) of **R$ 137.04**.
- **Regional Concentration**: São Paulo (**SP**) dominates the regional market, driving **~R$ 5.07M** in revenue (~38% of total revenue), aligning with its status as Brazil's primary economic center.
- **Customer Retention Gap**: Only **~3%** of customers are repeat buyers (2+ orders), yet they contribute a disproportionately larger **~5.5%** of total revenue. This highlights customer retention and post-purchase loyalty programs as primary growth opportunities.
- **Growth Trajectory**: Revenue expanded steadily from a small pilot in late 2016, experienced a pronounced spike in November 2017 driven by Black Friday demand, and stabilized at a sustained plateau of R$ 800k–R$ 980k per month through mid-2018.

---

## Dataset

This project uses the [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) hosted on Kaggle. It contains real, anonymized commercial data covering approximately 100,000 orders placed between 2016 and 2018 across multiple marketplaces in Brazil.

---

*Not currently deployed live — see "How to Run Locally" above.*

---

*Portfolio Project #2 — follows a completed SQL + Python sales analysis project (Project #1).*
