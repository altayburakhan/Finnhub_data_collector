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

CACHE_TTL = 1
REFRESH_INTERVAL = 1
DEFAULT_HOURS = 1
MAX_HOURS = 24

logger = logging.getLogger(__name__)

load_dotenv()

st.set_page_config(
    page_title="Stock Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .element-container {
            overflow: auto;
            max-height: calc(100vh - 100px);
        }
        .stApp {
            overflow: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_db_connection() -> Optional[Engine]:
    """Create database connection."""
    try:
        user = os.getenv("POSTGRES_USER")
        pwd = os.getenv("POSTGRES_PASSWORD")
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        db = os.getenv("POSTGRES_DB")

        url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
        return create_engine(url)
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_data(_engine: Engine, hours: int = DEFAULT_HOURS) -> pd.DataFrame:
    """Load data for last n hours."""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)

        fields = ["symbol", "price", "volume", "timestamp", "collected_at"]
        select_fields = ", ".join(fields)
        window_start = "AVG(price) OVER (PARTITION BY symbol"
        window_end = "ORDER BY collected_at "

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

        query = select_clause + window_clause + from_clause

        params = {"cutoff": cutoff_time}
        date_cols = ["timestamp", "collected_at"]

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
        st.metric("Son Fiyat", f"${last_price:.2f}", f"{change:.2f}")
    with col2:
        st.metric("Ortalama Fiyat", f"${symbol_data['price'].mean():.2f}")
    with col3:
        st.metric("İşlem Hacmi", f"{symbol_data['volume'].iloc[0]:,.0f}")


def create_chart(symbol_data: pd.DataFrame, symbol: str, timestamp: str) -> None:
    """Create price chart."""
    fig = go.Figure()

    price_trace = go.Scatter(
        x=symbol_data["collected_at"],
        y=symbol_data["price"],
        mode="lines",
        name="Price",
        line=dict(color="#2ecc71", width=2),
    )
    fig.add_trace(price_trace)

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
        uirevision=True,
    )
    st.plotly_chart(fig, use_container_width=True, key=f"chart_{symbol}")


def main() -> None:
    """Main application function."""
    engine = get_db_connection()
    if not engine:
        st.error("Database connection failed!")
        return

    st.title("📊 Stock Tracker Dashboard")

    with st.sidebar:
        slider_params = {
            "label": "Data Range (Hours)",
            "min_value": 1,
            "max_value": MAX_HOURS,
            "value": DEFAULT_HOURS,
            "key": "hours_slider"
        }
        hours = st.slider(**slider_params)
        update_time = st.empty()

    # Use session state to store a counter for unique keys
    if 'counter' not in st.session_state:
        st.session_state.counter = 0
    
    # Increment counter on each iteration
    def get_unique_key():
        st.session_state.counter += 1
        return str(st.session_state.counter)

    metrics_placeholder = st.empty()
    chart_placeholder = st.empty()
    table_placeholder = st.empty()

    df = load_data(engine, hours)
    if df.empty:
        st.warning("Data not found!")
        return

    symbols = sorted(df["symbol"].unique())
    symbol_container = st.sidebar.empty()
    selected_symbol = symbol_container.selectbox("Stock", symbols, key="symbol_select")

    while True:
        try:
            time_format = "%H:%M:%S.%f"
            current_time = datetime.now().strftime(time_format)[:-4]
            update_msg = f"Last update: {current_time}"
            update_time.text(update_msg)

            # Get a unique key for this iteration
            unique_key = get_unique_key()

            st.cache_data.clear()
            df = load_data(engine, hours)

            if df.empty:
                st.warning("Data not found!")
                time.sleep(REFRESH_INTERVAL)
                continue

            symbol_data = df[df["symbol"] == selected_symbol].copy()
            if not symbol_data.empty:
                symbol_data['display_time'] = (
                    symbol_data['collected_at'].dt.strftime('%H:%M:%S.%f').str[:-4]
                )

                with metrics_placeholder.container():
                    create_metrics(symbol_data, selected_symbol)

                with chart_placeholder.container():
                    # Use the unique key for this chart
                    fig = go.Figure()

                    price_trace = go.Scatter(
                        x=symbol_data["collected_at"],
                        y=symbol_data["price"],
                        mode="lines",
                        name="Price",
                        line=dict(color="#2ecc71", width=2),
                    )
                    fig.add_trace(price_trace)

                    ma_trace = go.Scatter(
                        x=symbol_data["collected_at"],
                        y=symbol_data["price_ma_5"],
                        mode="lines",
                        name="5dk MA",
                        line=dict(color="#3498db", width=1, dash="dash"),
                    )
                    fig.add_trace(ma_trace)

                    fig.update_layout(
                        title=f"{selected_symbol} Price Chart",
                        xaxis_title="Time",
                        yaxis_title="Price ($)",
                        template="plotly_dark",
                        height=500,
                        uirevision=True,
                    )
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{unique_key}")

                with table_placeholder.container():
                    display_df = symbol_data[["display_time", "price", "volume"]].copy()
                    display_df.columns = ["Time", "Price", "Volume"]
                    display_df["Price"] = display_df["Price"].map("${:,.2f}".format)
                    display_df["Volume"] = display_df["Volume"].map("{:,.0f}".format)
                    st.dataframe(
                        display_df.head(10),
                        height=400,
                        key=f"table_{unique_key}"
                    )

            time.sleep(REFRESH_INTERVAL / 2)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
