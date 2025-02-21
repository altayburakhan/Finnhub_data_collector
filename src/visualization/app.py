"""Data visualization application with Streamlit."""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine

# Constants
CACHE_TTL = 3  # seconds
REFRESH_INTERVAL = 3  # seconds
DEFAULT_HOURS = 1
MAX_HOURS = 24

# Logging configuration
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()


@st.cache_resource
def get_db_connection() -> Optional[Engine]:
    """Create database connection."""
    try:
        # Create database URL
        user = os.getenv("POSTGRES_USER")
        pwd = os.getenv("POSTGRES_PASSWORD")
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        db = os.getenv("POSTGRES_DB")

        # Create URL
        url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
        return create_engine(url)
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None


@st.cache_data(ttl=CACHE_TTL)
def load_data(_engine: Engine, hours: int = DEFAULT_HOURS) -> pd.DataFrame:
    """Load data for last n hours."""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Split SQL query into parts
        fields = ["symbol", "price", "volume", "timestamp", "collected_at"]
        select_fields = ", ".join(fields)
        window_start = "AVG(price) OVER (PARTITION BY symbol"
        window_end = "ORDER BY collected_at "

        # Join query parts
        select_base = f"SELECT {select_fields}"
        window_full = f"{window_start} {window_end}"
        select_clause = f"{select_base}, {window_full}"

        window_clause = (
            "RANGE BETWEEN INTERVAL '5 minutes' PRECEDING AND CURRENT ROW"
            ") as price_ma_5 "
        )
        from_clause = (
            "FROM stock_data "
            "WHERE collected_at > %(cutoff)s "
            "ORDER BY collected_at DESC"
        )

        # Join query parts
        query = select_clause + window_clause + from_clause

        # Prepare parameters
        params = {"cutoff": cutoff_time}
        date_cols = ["timestamp", "collected_at"]

        # Run query
        df = pd.read_sql_query(
            query,
            _engine,
            params=params,
            parse_dates=date_cols,
        )
        return df.copy()
    except Exception as e:
        st.error(f"Data loading error: {str(e)}")
        return pd.DataFrame()


def get_price_change(prices: pd.Series) -> tuple[float, float]:
    """Calculate price change."""
    last = prices.iloc[0]
    change = last - prices.iloc[-1]
    return last, change


def create_metrics(symbol_data: pd.DataFrame, symbol: str) -> None:
    """Show statistics metrics."""
    col1, col2, col3 = st.columns(3)
    with col1:
        last_price, change = get_price_change(symbol_data["price"])
        st.metric(
            "Son Fiyat",
            f"${last_price:.2f}",
            f"{change:.2f}",
            key=f"metric_price_{symbol}",
        )
    with col2:
        st.metric(
            "Ortalama Fiyat",
            f"${symbol_data['price'].mean():.2f}",
            key=f"metric_avg_{symbol}",
        )
    with col3:
        st.metric(
            "İşlem Hacmi",
            f"{symbol_data['volume'].iloc[0]:,.0f}",
            key=f"metric_volume_{symbol}",
        )


def create_chart(symbol_data: pd.DataFrame, symbol: str) -> None:
    """Create price chart."""
    fig = go.Figure()

    # Price line
    price_trace = go.Scatter(
        x=symbol_data["collected_at"],
        y=symbol_data["price"],
        mode="lines",
        name="Price",
        line=dict(color="#2ecc71", width=2),
    )
    fig.add_trace(price_trace)

    # Moving average line
    ma_trace = go.Scatter(
        x=symbol_data["collected_at"],
        y=symbol_data["price_ma_5"],
        mode="lines",
        name="5dk MA",
        line=dict(color="#3498db", width=1, dash="dash"),
    )
    fig.add_trace(ma_trace)

    fig.update_layout(
        title=f"{symbol} Price Chart",
        xaxis_title="Time",
        yaxis_title="Price ($)",
        template="plotly_dark",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True, key=f"chart_{symbol}")


def main() -> None:
    """Main application function."""
    page_config = {
        "page_title": "Stock Tracker",
        "page_icon": "📈",
        "layout": "wide",
    }
    st.set_page_config(**page_config)

    # Database connection
    engine = get_db_connection()
    if not engine:
        st.error("Database connection failed!")
        return

    # Main title
    st.title("📊 Stock Tracker Dashboard")

    # Sidebar controls
    with st.sidebar:
        slider_params = {
            "label": "Data Range (Hours)",
            "min_value": 1,
            "max_value": MAX_HOURS,
            "value": DEFAULT_HOURS,
            "key": "time_slider",
        }
        hours = st.slider(**slider_params)
        update_time = st.empty()

    # Create placeholders
    metrics_placeholder = st.empty()
    chart_placeholder = st.empty()
    table_placeholder = st.empty()

    # Load first data
    df = load_data(engine, hours)
    if df.empty:
        st.warning("Data not found!")
        return

    # Symbol selection - outside loop
    symbols = sorted(df["symbol"].unique())
    symbol_container = st.sidebar.empty()
    selected_symbol = symbol_container.selectbox("Stock", symbols, key="symbol_select")

    # Data loading and update loop
    while True:
        try:
            # Format last update time
            time_format = "%H:%M:%S"
            current_time = datetime.now().strftime(time_format)
            update_msg = f"Last update: {current_time}"
            update_time.text(update_msg)

            # Clear cache and reload data
            st.cache_data.clear()
            df = load_data(engine, hours)

            if df.empty:
                st.warning("Data not found!")
                time.sleep(REFRESH_INTERVAL)
                continue

            # Data for selected symbol
            symbol_data = df[df["symbol"] == selected_symbol]

            # Statistics
            with metrics_placeholder.container():
                create_metrics(symbol_data, selected_symbol)

            # Chart
            with chart_placeholder.container():
                create_chart(symbol_data, selected_symbol)

            # Table
            with table_placeholder.container():
                st.dataframe(
                    symbol_data[["collected_at", "price", "volume"]]
                    .rename(
                        columns={
                            "collected_at": "Time",
                            "price": "Price",
                            "volume": "Volume",
                        }
                    )
                    .head(10),
                    key=f"table_{selected_symbol}",
                )

            # Refresh interval
            time.sleep(REFRESH_INTERVAL)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
