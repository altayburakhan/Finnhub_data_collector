"""Streamlit ile veri görselleştirme uygulaması."""

from datetime import datetime, timedelta
import logging
import os
import time
from typing import Dict, List, Optional

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
        db_url = (
            f"postgresql://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@"
            f"{os.getenv('POSTGRES_HOST')}:"
            f"{os.getenv('POSTGRES_PORT')}/"
            f"{os.getenv('POSTGRES_DB')}"
        )
        return create_engine(db_url)
    except Exception as e:
        st.error(f"Veritabanı bağlantı hatası: {str(e)}")
        return None


@st.cache_data(ttl=CACHE_TTL)
def load_data(_engine: Engine, hours: int = DEFAULT_HOURS) -> pd.DataFrame:
    """Son n saatlik veriyi yükle."""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        query = """
        SELECT 
            symbol,
            price,
            volume,
            timestamp,
            collected_at,
            AVG(price) OVER (
                PARTITION BY symbol 
                ORDER BY collected_at 
                RANGE BETWEEN INTERVAL '5 minutes' PRECEDING AND CURRENT ROW
            ) as price_ma_5
        FROM stock_data 
        WHERE collected_at > %(cutoff)s
        ORDER BY collected_at DESC
        """
        
        return pd.read_sql_query(
            query, 
            _engine,
            params={'cutoff': cutoff_time},
            parse_dates=['timestamp', 'collected_at']
        )
    except Exception as e:
        st.error(f"Veri yükleme hatası: {str(e)}")
        return pd.DataFrame()


def create_metrics(symbol_data: pd.DataFrame) -> None:
    """
    İstatistik metriklerini göster.

    Args:
        symbol_data: Seçili sembol için veriler
    """
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Son Fiyat",
            f"${symbol_data['price'].iloc[0]:.2f}",
            f"{(symbol_data['price'].iloc[0] - symbol_data['price'].iloc[-1]):.2f}"
        )
    with col2:
        st.metric(
            "Ortalama Fiyat",
            f"${symbol_data['price'].mean():.2f}"
        )
    with col3:
        st.metric(
            "İşlem Hacmi",
            f"{symbol_data['volume'].iloc[0]:,.0f}"
        )


def create_chart(symbol_data: pd.DataFrame, symbol: str) -> None:
    """
    Fiyat grafiğini oluştur.

    Args:
        symbol_data: Seçili sembol için veriler
        symbol: Hisse senedi sembolü
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=symbol_data['collected_at'],
        y=symbol_data['price'],
        mode='lines',
        name='Fiyat',
        line=dict(color='#2ecc71', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=symbol_data['collected_at'],
        y=symbol_data['price_ma_5'],
        mode='lines',
        name='5dk MA',
        line=dict(color='#3498db', width=1, dash='dash')
    ))
    fig.update_layout(
        title=f"{symbol} Fiyat Grafiği",
        xaxis_title="Zaman",
        yaxis_title="Fiyat ($)",
        template="plotly_dark",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)


def main():
    """Ana uygulama fonksiyonu."""
    st.set_page_config(
        page_title="Hisse Senedi Takip",
        page_icon="📈",
        layout="wide"
    )
    
    # Veritabanı bağlantısı
    engine = get_db_connection()
    if not engine:
        st.error("Veritabanına bağlanılamadı!")
        return

    # Ana başlık
    st.title("📊 Hisse Senedi Takip Paneli")

    # Sidebar kontrolleri
    with st.sidebar:
        hours = st.slider(
            "Veri Aralığı (Saat)",
            1,
            MAX_HOURS,
            DEFAULT_HOURS,
            key="time_slider"
        )

    # İlk veriyi yükle
    df = load_data(engine, hours)
    if df.empty:
        st.warning("Veri bulunamadı!")
        return

    # Sembol seçimi - döngü dışında
    symbols = sorted(df['symbol'].unique())
    symbol_container = st.sidebar.empty()
    selected_symbol = symbol_container.selectbox(
        "Hisse Senedi",
        symbols,
        key="symbol_select"
    )

    # Veri yükleme ve güncelleme döngüsü
    placeholder = st.empty()
    while True:
        try:
            # Son güncelleme zamanı
            st.sidebar.text(
                f"Son güncelleme: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            # Veri yükleme
            df = load_data(engine, hours)
            
            if df.empty:
                placeholder.warning("Veri bulunamadı!")
                time.sleep(REFRESH_INTERVAL)
                continue
            
            # Ana içerik
            with placeholder.container():
                # Seçilen sembol için veri
                symbol_data = df[df['symbol'] == selected_symbol]
                
                # İstatistikler
                create_metrics(symbol_data)
                
                # Grafik
                create_chart(symbol_data, selected_symbol)
                
                # Tablo
                st.dataframe(
                    symbol_data[['collected_at', 'price', 'volume']]
                    .rename(columns={
                        'collected_at': 'Zaman',
                        'price': 'Fiyat',
                        'volume': 'Hacim'
                    })
                    .head(10)
                )
            
            # Yenileme aralığı
            time.sleep(REFRESH_INTERVAL)
            
        except Exception as e:
            st.error(f"Bir hata oluştu: {str(e)}")
            time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()