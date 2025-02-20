import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import plotly.graph_objects as go
from datetime import datetime, timedelta
import plotly.express as px
from typing import Dict, List, Optional

# .env dosyasını yükle
load_dotenv()

def get_db_connection() -> create_engine:
    """Veritabanı bağlantısı oluştur"""
    db_url = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(db_url)

def load_data(engine: create_engine, hours: int = 1) -> pd.DataFrame:
    """
    Veritabanından veri yükle
    
    Args:
        engine: SQLAlchemy engine
        hours: Kaç saatlik veri çekileceği
        
    Returns:
        DataFrame: Yüklenen veriler
    """
    query = f"""
    SELECT symbol, price, volume, timestamp, collected_at 
    FROM stock_data 
    WHERE collected_at > NOW() - INTERVAL '{hours} hours'
    ORDER BY collected_at DESC
    """
    return pd.read_sql(query, engine)

def create_price_chart(data: pd.DataFrame, symbol: str) -> go.Figure:
    """
    Fiyat grafiği oluştur
    
    Args:
        data: Veri DataFrame'i
        symbol: Hisse senedi sembolü
        
    Returns:
        Figure: Plotly grafik objesi
    """
    symbol_data = data[data['symbol'] == symbol].copy()
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=symbol_data['collected_at'],
        y=symbol_data['price'],
        mode='lines+markers',
        name='Fiyat',
        line=dict(color='#2ecc71', width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title=f"{symbol} Fiyat Grafiği",
        xaxis_title="Zaman",
        yaxis_title="Fiyat ($)",
        template="plotly_dark",
        hovermode='x unified'
    )
    return fig

def show_statistics(data: pd.DataFrame, symbol: str) -> None:
    """İstatistikleri göster"""
    symbol_data = data[data['symbol'] == symbol]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_price = symbol_data['price'].iloc[0]
        st.metric("Güncel Fiyat", f"${current_price:.2f}")
        
    with col2:
        avg_price = symbol_data['price'].mean()
        st.metric("Ortalama", f"${avg_price:.2f}")
        
    with col3:
        min_price = symbol_data['price'].min()
        st.metric("En Düşük", f"${min_price:.2f}")
        
    with col4:
        max_price = symbol_data['price'].max()
        st.metric("En Yüksek", f"${max_price:.2f}")

def main():
    st.set_page_config(
        page_title="Hisse Senedi Takip",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 Hisse Senedi Takip Paneli")
    
    try:
        # Veritabanı bağlantısı
        engine = get_db_connection()
        
        # Zaman aralığı seçimi
        hours = st.sidebar.slider(
            "Veri Aralığı (Saat)",
            min_value=1,
            max_value=24,
            value=1
        )
        
        # Verileri yükle
        df = load_data(engine, hours)
        
        if df.empty:
            st.warning("Henüz veri bulunmamaktadır.")
            return
            
        # Sembol seçimi
        symbols = sorted(df['symbol'].unique())
        selected_symbol = st.sidebar.selectbox("Hisse Senedi", symbols)
        
        # İstatistikler
        st.subheader("📊 İstatistikler")
        show_statistics(df, selected_symbol)
        
        # Fiyat grafiği
        st.subheader("💹 Fiyat Grafiği")
        fig = create_price_chart(df, selected_symbol)
        st.plotly_chart(fig, use_container_width=True)
        
        # Son işlemler tablosu
        st.subheader("📝 Son İşlemler")
        recent_data = df[df['symbol'] == selected_symbol].head(10)
        st.dataframe(
            recent_data[['collected_at', 'price', 'volume']]
            .rename(columns={
                'collected_at': 'Zaman',
                'price': 'Fiyat',
                'volume': 'Hacim'
            })
        )
        
        # Auto-refresh
        st.sidebar.write("---")
        if st.sidebar.checkbox("Otomatik Yenile", value=True):
            st.experimental_rerun()
            
    except Exception as e:
        st.error(f"Bir hata oluştu: {str(e)}")

if __name__ == "__main__":
    main()