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
    def __init__(self, db_name="borsa_terminali_v2.db"):
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
    def calculate_rsi(df, period=14):
        """
        Göreceli Güç Endeksi (RSI) hesaplar. 
        Aşırı alım/satım bölgelerini belirlemek için kullanılır.
        """
        try:
            # Fiyat değişimlerini bul
            delta = df['Close'].diff()
            
            # Kazanç ve kayıpları ayır
            gain = (delta.where(delta > 0, 0))
            loss = (-delta.where(delta < 0, 0))
            
            # Ortalama kazanç ve kaybı hesapla (EMA yöntemi)
            avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
            avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
            
            # Göreceli Güç (RS) ve RSI hesaplama
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            return df
        except Exception as e:
            st.error(f"RSI hesaplama hatası: {e}")
            return df

    @staticmethod
    def calculate_monte_carlo(df, days=30, simulations=1000):
        try:
            # Logaritmik getiriler
            returns = np.log(df['Close'] / df['Close'].shift(1)).dropna()
            last_price = float(df['Close'].iloc[-1])
            mu, sigma = returns.mean(), returns.std()
            
            # Vektörize edilmiş Geometrik Brown Hareketi
            shocks = np.exp((mu - 0.5 * sigma**2) + sigma * np.random.standard_normal((days, simulations)))
            paths = np.vstack([np.ones(simulations) * last_price, shocks])
            return pd.DataFrame(np.cumprod(paths, axis=0))
        except Exception as e:
            st.error(f"Monte Carlo hatası: {e}")
            return pd.DataFrame()

# =================================================================
# UI COMPONENTS (ARAYÜZ BİLEŞENLERİ)
# =================================================================
def main():
    st.set_page_config(page_title="Borsa Pro-Terminal V2.1", layout="wide", initial_sidebar_state="expanded")
    
    # Başlatıcılar
    db = DatabaseManager()
    engine = FinanceEngine()
    
    # Custom CSS - Stil ayarları
    st.markdown("""
        <style>
        .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4256; }
        .main-header { font-size: 2.5rem; font-weight: bold; color: #00d4ff; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="main-header">🚀 Borsa Stratejik Karar Terminali V2.1</p>', unsafe_allow_html=True)
    
    # Sidebar - Kullanıcı ve Giriş Paneli
    with st.sidebar:
        st.header("👤 Kullanıcı Paneli")
        user_name = st.text_input("Kullanıcı Adı", value="Admin").strip()
        
        st.divider()
        st.header("🔍 Sembol Sorgu")
        symbol_input = st.text_input("Hisse Kodu (Örn: EREGL.IS)", value="THYAO.IS").upper()
        
        if st.button("➕ İzleme Listesine Ekle"):
            if db.add_to_watchlist(user_name, symbol_input):
                st.toast(f"{symbol_input} başarıyla eklendi!")
        
        st.divider()
        st.header("📋 İzleme Listem")
        my_list = db.get_watchlist(user_name)
        if my_list:
            selected_from_list = st.selectbox("Hızlı Seçim", options=my_list)
            if st.button("🗑️ Listeden Kaldır"):
                db.remove_from_watchlist(user_name, selected_from_list)
                st.rerun()
        else:
            st.info("Listeniz henüz boş.")

    # ANA EKRAN AKIŞI
    if symbol_input:
        with st.spinner(f"{symbol_input} verileri analiz ediliyor..."):
            # 1. Veri Çekme
            df = engine.get_stock_data(symbol_input)
            
            if df is not None:
                # 2. Teknik Analiz (RSI Ekleme)
                df = engine.calculate_rsi(df)

                # 3. ÖZET METRİKLER (Üst Kartlar)
                c1, c2, c3, c4 = st.columns(4)
                last_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                change_pct = ((last_price / prev_price) - 1) * 100
                current_rsi = df['RSI'].iloc[-1]
                
                c1.metric("Son Fiyat", f"{last_price:.2f} TL", f"{change_pct:.2f}%")
                c2.metric("Günlük Hacim", f"{df['Volume'].iloc[-1]:,.0f}")
                c3.metric("RSI (14)", f"{current_rsi:.2f}")
                c4.metric("Yıllık Zirve", f"{df['High'].max():.2f} TL")

                # 4. GRAFİK VE ANALİZ SEKMELERİ
                tab_chart, tab_monte, tab_corr = st.tabs(["📈 Fiyat & RSI Grafiği", "🎲 Monte Carlo Simülasyonu", "🔗 Korelasyon Analizi"])
                
                with tab_chart:
                    # Mum Grafiği
                    fig_main = go.Figure()
                    fig_main.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                                     low=df['Low'], close=df['Close'], name="Fiyat"))
                    fig_main.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, title=f"{symbol_input} Mum Grafiği")
                    st.plotly_chart(fig_main, use_container_width=True)

                    # RSI Alt Grafik
                    fig_rsi = go.Figure()
                    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta', width=1.5)))
                    # RSI Eşik Çizgileri
                    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Aşırı Alım (70)")
                    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Aşırı Satım (30)")
                    fig_rsi.update_layout(template="plotly_dark", height=250, title="RSI (Göreceli Güç Endeksi)")
                    st.plotly_chart(fig_rsi, use_container_width=True)

                with tab_monte:
                    st.subheader("30 Günlük Fiyat Tahmin Projeksiyonu")
                    col_mc_left, col_mc_right = st.columns([3, 1])
                    
                    mc_results = engine.calculate_monte_carlo(df)
                    if not mc_results.empty:
                        with col_mc_left:
                            fig_mc = go.Figure()
                            # Performans için ilk 100 senaryo
                            for i in range(min(100, 1000)):
                                fig_mc.add_trace(go.Scatter(y=mc_results[i], mode='lines', 
                                                           line=dict(width=0.5), opacity=0.15, showlegend=False))
                            
                            mean_path = mc_results.mean(axis=1)
                            fig_mc.add_trace(go.Scatter(y=mean_path, name="Beklenen Değer", line=dict(color='gold', width=3)))
                            fig_mc.update_layout(template="plotly_dark", height=500, yaxis_title="Fiyat (TL)", xaxis_title="Gün")
                            st.plotly_chart(fig_mc, use_container_width=True)
                        
                        with col_mc_right:
                            st.write("#### 📊 Risk İstatistikleri")
                            target_10 = last_price * 1.10
                            prob_up = (mc_results.iloc[-1] > target_10).mean() * 100
                            var_95 = np.percentile(mc_results.iloc[-1], 5)
                            
                            st.metric("10% Yükseliş İhtimali", f"%{prob_up:.1f}")
                            st.metric("En Kötü Senaryo (VaR)", f"{var_95:.2f} TL")
                            
                            if current_rsi < 30:
                                st.success("💡 RSI: Aşırı Satım (Fırsat olabilir)")
                            elif current_rsi > 70:
                                st.error("⚠️ RSI: Aşırı Alım (Düzeltme gelebilir)")

                with tab_corr:
                    st.subheader("Piyasa Enstrümanları ile İlişki Matrisi")
                    other_assets = ["XU100.IS", "USDTRY=X", "GC=F", "BTC-USD"]
                    corr_data = pd.DataFrame({symbol_input: df['Close']})
                    
                    with st.spinner("Korelasyon verileri çekiliyor..."):
                        for asset in other_assets:
                            a_df = engine.get_stock_data(asset)
                            if a_df is not None:
                                corr_data[asset] = a_df['Close']
                        
                        matrix = corr_data.dropna().pct_change().corr()
                        fig_heat = px.imshow(matrix, text_auto=".2f", color_continuous_scale='RdBu_r', title="Korelasyon Isı Haritası")
                        fig_heat.update_layout(template="plotly_dark")
                        st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.error("Sembol verisi çekilemedi. Lütfen internet bağlantınızı ve sembolü (.IS eki dahil) kontrol edin.")

if __name__ == "__main__":
    main()
