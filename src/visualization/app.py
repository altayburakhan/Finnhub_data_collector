"""Streamlit ile veri görselleştirme uygulaması."""

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

# Sabitler
CACHE_TTL = 3  # saniye
REFRESH_INTERVAL = 3  # saniye
DEFAULT_HOURS = 1
MAX_HOURS = 24

# Log yapılandırması
logger = logging.getLogger(__name__)

# .env dosyasını yükle
load_dotenv()


@st.cache_resource
def get_db_connection() -> Optional[Engine]:
    """Veritabanı bağlantısı oluştur."""
    try:
        # Veritabanı URL'sini parçalı oluştur
        user = os.getenv("POSTGRES_USER")
        pwd = os.getenv("POSTGRES_PASSWORD")
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        db = os.getenv("POSTGRES_DB")

        # URL'yi oluştur
        url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
        return create_engine(url)
    except Exception as e:
        st.error(f"Veritabanı bağlantı hatası: {str(e)}")
        return None


@st.cache_data(ttl=CACHE_TTL)
def load_data(_engine: Engine, hours: int = DEFAULT_HOURS) -> pd.DataFrame:
    """Son n saatlik veriyi yükle."""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # SQL sorgusunu parçalara böl
        fields = ["symbol", "price", "volume", "timestamp", "collected_at"]
        select_fields = ", ".join(fields)
        window_start = "AVG(price) OVER (PARTITION BY symbol"
        window_end = "ORDER BY collected_at "

        # Sorgu parçalarını birleştir
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

        # Sorguyu birleştir
        query = select_clause + window_clause + from_clause

        # Parametreleri hazırla
        params = {"cutoff": cutoff_time}
        date_cols = ["timestamp", "collected_at"]

        # Sorguyu çalıştır
        df = pd.read_sql_query(
            query,
            _engine,
            params=params,
            parse_dates=date_cols,
        )
        return df.copy()
    except Exception as e:
        st.error(f"Veri yükleme hatası: {str(e)}")
        return pd.DataFrame()


def get_price_change(prices: pd.Series) -> tuple[float, float]:
    """Fiyat değişimini hesapla."""
    last = prices.iloc[0]
    change = last - prices.iloc[-1]
    return last, change


def create_metrics(symbol_data: pd.DataFrame) -> None:
    """İstatistik metriklerini göster."""
    col1, col2, col3 = st.columns(3)
    with col1:
        last_price, change = get_price_change(symbol_data["price"])
        st.metric("Son Fiyat", f"${last_price:.2f}", f"{change:.2f}")
    with col2:
        st.metric("Ortalama Fiyat", f"${symbol_data['price'].mean():.2f}")
    with col3:
        st.metric("İşlem Hacmi", f"{symbol_data['volume'].iloc[0]:,.0f}")


def create_chart(symbol_data: pd.DataFrame, symbol: str) -> None:
    """Fiyat grafiğini oluştur."""
    fig = go.Figure()

    # Fiyat çizgisi
    price_trace = go.Scatter(
        x=symbol_data["collected_at"],
        y=symbol_data["price"],
        mode="lines",
        name="Fiyat",
        line=dict(color="#2ecc71", width=2),
    )
    fig.add_trace(price_trace)

    # Hareketli ortalama çizgisi
    ma_trace = go.Scatter(
        x=symbol_data["collected_at"],
        y=symbol_data["price_ma_5"],
        mode="lines",
        name="5dk MA",
        line=dict(color="#3498db", width=1, dash="dash"),
    )
    fig.add_trace(ma_trace)

    fig.update_layout(
        title=f"{symbol} Fiyat Grafiği",
        xaxis_title="Zaman",
        yaxis_title="Fiyat ($)",
        template="plotly_dark",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    """Ana uygulama fonksiyonu."""
    page_config = {
        "page_title": "Hisse Senedi Takip",
        "page_icon": "📈",
        "layout": "wide",
    }
    st.set_page_config(**page_config)

    # Veritabanı bağlantısı
    engine = get_db_connection()
    if not engine:
        st.error("Veritabanına bağlanılamadı!")
        return

    # Ana başlık
    st.title("📊 Hisse Senedi Takip Paneli")

    # Sidebar kontrolleri
    with st.sidebar:
        slider_params = {
            "label": "Veri Aralığı (Saat)",
            "min_value": 1,
            "max_value": MAX_HOURS,
            "value": DEFAULT_HOURS,
            "key": "time_slider",
        }
        hours = st.slider(**slider_params)
        update_time = st.empty()

    # Placeholder'ları oluştur
    metrics_placeholder = st.empty()
    chart_placeholder = st.empty()
    table_placeholder = st.empty()

    # İlk veriyi yükle
    df = load_data(engine, hours)
    if df.empty:
        st.warning("Veri bulunamadı!")
        return

    # Sembol seçimi - döngü dışında
    symbols = sorted(df["symbol"].unique())
    symbol_container = st.sidebar.empty()
    selected_symbol = symbol_container.selectbox(
        "Hisse Senedi", symbols, key="symbol_select"
    )

    # Veri yükleme ve güncelleme döngüsü
    while True:
        try:
            # Son güncelleme zamanını formatla
            time_format = "%H:%M:%S"
            current_time = datetime.now().strftime(time_format)
            update_msg = f"Son güncelleme: {current_time}"
            update_time.text(update_msg)

            # Cache'i temizle ve veriyi yeniden yükle
            st.cache_data.clear()
            df = load_data(engine, hours)

            if df.empty:
                st.warning("Veri bulunamadı!")
                time.sleep(REFRESH_INTERVAL)
                continue

            # Seçilen sembol için veri
            symbol_data = df[df["symbol"] == selected_symbol]

            # İstatistikler
            with metrics_placeholder.container():
                create_metrics(symbol_data)

            # Grafik
            with chart_placeholder.container():
                create_chart(symbol_data, selected_symbol)

            # Tablo
            with table_placeholder.container():
                st.dataframe(
                    symbol_data[["collected_at", "price", "volume"]]
                    .rename(
                        columns={
                            "collected_at": "Zaman",
                            "price": "Fiyat",
                            "volume": "Hacim",
                        }
                    )
                    .head(10)
                )

            # Yenileme aralığı
            time.sleep(REFRESH_INTERVAL)

        except Exception as e:
            st.error(f"Bir hata oluştu: {str(e)}")
            time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
