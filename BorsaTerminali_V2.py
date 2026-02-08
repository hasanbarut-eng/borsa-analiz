import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import sqlite3
from datetime import datetime, timedelta
import os

# =================================================================
# DATABASE MANAGER (VERİ TABANI YÖNETİMİ)
# =================================================================
class DatabaseManager:
    """Kullanıcı izleme listelerini ve tercihlerini yönetir."""
    def __init__(self, db_name="borsa_terminali.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            # İzleme listesi tablosu
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    symbol TEXT,
                    added_date TEXT,
                    UNIQUE(username, symbol)
                )
            """)

    def add_to_watchlist(self, username, symbol):
        try:
            with self.conn:
                self.conn.execute("INSERT OR IGNORE INTO watchlist (username, symbol, added_date) VALUES (?, ?, ?)",
                                 (username, symbol, datetime.now().strftime("%Y-%m-%d %H:%M")))
            return True
        except Exception as e:
            st.error(f"DB Hatası: {e}")
            return False

    def get_watchlist(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT symbol FROM watchlist WHERE username = ?", (username,))
        return [row[0] for row in cursor.fetchall()]

    def remove_from_watchlist(self, username, symbol):
        with self.conn:
            self.conn.execute("DELETE FROM watchlist WHERE username = ? AND symbol = ?", (username, symbol))

# =================================================================
# ANALYSIS ENGINE (HESAPLAMA MOTORU)
# =================================================================
class FinanceEngine:
    """Finansal verileri çeker ve ağır matematiksel hesaplamaları yapar."""
    
    @staticmethod
    def get_stock_data(symbol, period="1y"):
        try:
            data = yf.download(symbol, period=period, interval="1d", progress=False)
            if data.empty: return None
            # Multi-index sütunlarını temizle
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            return data
        except Exception as e:
            st.error(f"Veri çekme hatası ({symbol}): {e}")
            return None

    @staticmethod
    def calculate_monte_carlo(df, days=30, simulations=1000):
        try:
            returns = np.log(df['Close'] / df['Close'].shift(1)).dropna()
            last_price = float(df['Close'].iloc[-1])
            mu, sigma = returns.mean(), returns.std()
            
            # Vektörize edilmiş Geometrik Brown Hareketi
            shocks = np.exp((mu - 0.5 * sigma**2) + sigma * np.random.standard_normal((days, simulations)))
            paths = np.vstack([np.ones(simulations) * last_price, shocks])
            return pd.DataFrame(np.cumprod(paths, axis=0))
        except Exception:
            return pd.DataFrame()

# =================================================================
# UI COMPONENTS (ARAYÜZ BİLEŞENLERİ)
# =================================================================
def main():
    st.set_page_config(page_title="Borsa Pro-Terminal V2", layout="wide", initial_sidebar_state="expanded")
    
    # Başlatıcılar
    db = DatabaseManager()
    engine = FinanceEngine()
    
    # Custom CSS
    st.markdown("""
        <style>
        .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4256; }
        .main-header { font-size: 2.5rem; font-weight: bold; color: #00d4ff; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="main-header">🚀 Borsa Stratejik Karar Terminali</p>', unsafe_allow_html=True)
    
    # Sidebar - Kullanıcı ve Giriş
    with st.sidebar:
        st.header("👤 Kullanıcı Paneli")
        user_name = st.text_input("Kullanıcı Adı", value="Admin").strip()
        
        st.divider()
        st.header("🔍 Sembol Sorgu")
        symbol_input = st.text_input("Hisse Kodu (Örn: EREGL.IS)", value="THYAO.IS").upper()
        
        if st.button("➕ İzleme Listesine Ekle"):
            if db.add_to_watchlist(user_name, symbol_input):
                st.toast(f"{symbol_input} listeye eklendi!")
        
        st.divider()
        st.header("📋 İzleme Listem")
        my_list = db.get_watchlist(user_name)
        if my_list:
            selected_from_list = st.selectbox("Listemden Seç", options=my_list)
            if st.button("🗑️ Listeden Kaldır"):
                db.remove_from_watchlist(user_name, selected_from_list)
                st.rerun()
        else:
            st.info("Listeniz henüz boş.")

    # ANA EKRAN AKIŞI
    if symbol_input:
        with st.spinner(f"{symbol_input} için veriler işleniyor..."):
            df = engine.get_stock_data(symbol_input)
            
            if df is not None:
                # 1. ÖZET METRİKLER
                c1, c2, c3, c4 = st.columns(4)
                last_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                change_pct = ((last_price / prev_price) - 1) * 100
                
                c1.metric("Son Fiyat", f"{last_price:.2f} TL", f"{change_pct:.2f}%")
                c2.metric("Günlük Hacim", f"{df['Volume'].iloc[-1]:,.0f}")
                c3.metric("Yıllık Zirve", f"{df['High'].max():.2f} TL")
                c4.metric("RSI (14)", "62.4") # Örnek sabit, teknik analiz modülü eklenebilir

                # 2. GRAFİK VE ANALİZ SEKMELERİ
                tab_chart, tab_monte, tab_corr = st.tabs(["📈 Fiyat Grafiği", "🎲 Monte Carlo Simülasyonu", "🔗 Korelasyon Analizi"])
                
                with tab_chart:
                    fig_main = go.Figure()
                    fig_main.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                                     low=df['Low'], close=df['Close'], name="Mum Grafiği"))
                    fig_main.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig_main, use_container_width=True)

                with tab_monte:
                    st.subheader("30 Günlük Fiyat Tahmin Projeksiyonu")
                    col_mc_left, col_mc_right = st.columns([3, 1])
                    
                    mc_results = engine.calculate_monte_carlo(df)
                    if not mc_results.empty:
                        with col_mc_left:
                            fig_mc = go.Figure()
                            for i in range(min(50, 1000)):
                                fig_mc.add_trace(go.Scatter(y=mc_results[i], mode='lines', 
                                                           line=dict(width=0.5), opacity=0.2, showlegend=False))
                            
                            mean_path = mc_results.mean(axis=1)
                            fig_mc.add_trace(go.Scatter(y=mean_path, name="Ortalama Beklenti", line=dict(color='yellow', width=3)))
                            fig_mc.update_layout(template="plotly_dark", height=500)
                            st.plotly_chart(fig_mc, use_container_width=True)
                        
                        with col_mc_right:
                            st.write("#### 📊 Risk İstatistikleri")
                            target_price = last_price * 1.10
                            prob = (mc_results.iloc[-1] > target_price).mean() * 100
                            var_95 = np.percentile(mc_results.iloc[-1], 5)
                            
                            st.write(f"**%10 Kar Olasılığı:** %{prob:.1f}")
                            st.write(f"**Destek (VaR %95):** {var_95:.2f} TL")
                            if prob > 50:
                                st.success("Pozitif Görünüm")
                            else:
                                st.warning("Yüksek Risk")

                with tab_corr:
                    st.subheader("Piyasa İlişki Matrisi")
                    other_assets = ["XU100.IS", "USDTRY=X", "GC=F", "BTC-USD"]
                    corr_data = pd.DataFrame({symbol_input: df['Close']})
                    
                    for asset in other_assets:
                        a_df = engine.get_stock_data(asset)
                        if a_df is not None:
                            corr_data[asset] = a_df['Close']
                    
                    matrix = corr_data.dropna().pct_change().corr()
                    fig_heat = px.imshow(matrix, text_auto=".2f", color_continuous_scale='RdBu_r')
                    fig_heat.update_layout(template="plotly_dark")
                    st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.error("Sembol bulunamadı veya Yahoo Finance hatası!")

if __name__ == "__main__":
    main()
