import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import sqlite3
from datetime import datetime

# =================================================================
# 1. DATABASE & STORAGE (GÜVENLİ HAFIZA VE PORTFÖY)
# =================================================================
class TerminalDB:
    """Kullanıcı portföyünü ve ayarlarını kalıcı olarak saklar."""
    def __init__(self, db_name="komuta_merkezi_v3.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        with self.conn:
            self.conn.execute("""CREATE TABLE IF NOT EXISTS portfolio 
                (symbol TEXT PRIMARY KEY, qty REAL, cost REAL)""")

    def save_p(self, s, q, c):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO portfolio VALUES (?,?,?)", (s, q, c))

    def get_p(self):
        return pd.read_sql_query("SELECT * FROM portfolio", self.conn)

    def delete_p(self, s):
        with self.conn:
            self.conn.execute("DELETE FROM portfolio WHERE symbol = ?", (s,))

# =================================================================
# 2. INTELLIGENCE ENGINE (ANALİZ VE TERCÜME MOTORU)
# =================================================================
class AnalystEngine:
    """Karmaşık veriyi basit Türkçe kararlara dönüştüren zeka katmanı."""
    
    @staticmethod
    def get_full_analysis(symbol):
        """Hisse verisini çeker ve analiz hazırlar."""
        try:
            # Canlı Veri Çekme
            df = yf.download(symbol, period="2y", interval="1d", progress=False)
            if df.empty: return None, None, None
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # Teknik Hesaplamalar
            df['SMA_50'] = df['Close'].rolling(50).mean()
            df['SMA_200'] = df['Close'].rolling(200).mean()
            delta = df['Close'].diff()
            g = delta.where(delta > 0, 0).rolling(14).mean()
            l = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g / l)))

            # Temel Veriler
            t = yf.Ticker(symbol)
            info = t.info
            fund = {
                "FK": info.get('trailingPE', 0),
                "PDDD": info.get('priceToBook', 0),
                "Temettu": info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                "Is_Ismi": info.get('longName', symbol)
            }
            
            return df, fund, t.news[:5]
        except Exception as e:
            st.error(f"Analiz hatası: {e}")
            return None, None, None

    @staticmethod
    def generate_simple_decision(df, fund):
        """Matematik öğretmeni için basit karar özeti."""
        last_c = df['Close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        sma50 = df['SMA_50'].iloc[-1]
        sma200 = df['SMA_200'].iloc[-1]
        
        score = 0
        reasons = []

        # 1. Trend Analizi
        if last_c > sma50:
            score += 2; reasons.append("✅ Fiyat yükseliş trendinde (SMA50 üstü).")
        else:
            score -= 1; reasons.append("⚠️ Fiyat kısa vadeli düşüş baskısında.")

        # 2. RSI (Hız) Analizi
        if rsi < 35:
            score += 2; reasons.append("🟢 Hisse çok ucuzlamış (RSI), alım fırsatı olabilir.")
        elif rsi > 75:
            score -= 2; reasons.append("🔴 Hisse çok şişmiş (RSI), düzeltme gelebilir.")

        # 3. Temel Analiz (Ucuzluk)
        if fund['FK'] != 0 and fund['FK'] < 15:
            score += 1; reasons.append(f"💎 Şirket kazancına göre ucuz görünüyor (F/K: {fund['FK']:.1f}).")

        # Karar Çıktısı
        if score >= 3: d, color = "GÜÇLÜ AL", "#00FF00"
        elif 1 <= score < 3: d, color = "OLUMLU / TUT", "#00D4FF"
        elif -1 <= score < 1: d, color = "NÖTR / BEKLE", "#FFFF00"
        else: d, color = "RİSKLİ / SAT", "#FF0000"

        return d, reasons, color

# =================================================================
# 3. MASTER UI (KULLANICI ARAYÜZÜ)
# =================================================================
def main():
    st.set_page_config(page_title="Pro-Terminal V3", layout="wide")
    db = TerminalDB()
    ae = AnalystEngine()

    # CSS Tasarımı
    st.markdown("""<style>
        .stMetric { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; }
        .decision-card { padding: 25px; border-radius: 15px; margin-bottom: 25px; color: white; }
    </style>""", unsafe_allow_html=True)

    st.title("🛡️ Borsa Stratejik Karar Terminali")

    # SIDEBAR: PORTFÖY GİRİŞİ
    with st.sidebar:
        st.header("💼 Portföy Yönetimi")
        s_in = st.text_input("Hisse Kodu (.IS ekleyin)", value="THYAO.IS").upper()
        q_in = st.number_input("Adet", min_value=0.0, value=100.0)
        c_in = st.number_input("Maliyet (TL)", min_value=0.0, value=250.0)
        if st.button("Portföye Kaydet"):
            db.save_p(s_in, q_in, c_in)
            st.rerun()
        
        st.divider()
        st.write("📋 **Kayıtlı Portföyüm**")
        p_df = db.get_p()
        if not p_df.empty:
            for s in p_df['symbol']:
                if st.button(f"Sil: {s}"):
                    db.delete_p(s); st.rerun()

    # ANA EKRAN: DASHBOARD
    if not p_df.empty:
        st.subheader("🏦 Portföy Özet Ekranı")
        total_v, total_p = 0, 0
        cols = st.columns(len(p_df))
        
        for i, row in p_df.iterrows():
            live = yf.download(row['symbol'], period="2d", progress=False)
            if not live.empty:
                curr = live['Close'].iloc[-1]
                val = curr * row['qty']; pnl = (curr - row['cost']) * row['qty']
                total_v += val; total_p += pnl
                with cols[i]:
                    st.metric(row['symbol'], f"{curr:.2f} TL", f"{pnl:,.0f} TL")
        
        st.success(f"**Toplam Varlık:** {total_v:,.2f} TL | **Net Kar/Zarar:** {total_p:,.2f} TL")

    # MODÜL: AKILLI ANALİZ
    st.divider()
    active_s = st.selectbox("Analiz İçin Hisse Seç", options=p_df['symbol'].tolist() if not p_df.empty else ["THYAO.IS"])
    
    if active_s:
        df, fund, news = ae.get_full_analysis(active_s)
        if df is not None:
            # KARAR KARTINI BASALIM
            dec, reasons, color = ae.generate_simple_decision(df, fund)
            st.markdown(f"""<div class="decision-card" style="background-color: {color}33; border: 2px solid {color};">
                <h2 style="color: {color};">🤖 Sistem Kararı: {dec}</h2>
                <ul style="font-size: 1.2rem;">{''.join([f"<li>{r}</li>" for r in reasons])}</ul>
            </div>""", unsafe_allow_html=True)

            # SEKMELER
            t_chart, t_fund, t_risk = st.tabs(["📈 Teknik Görünüm", "🏢 Şirket Sağlığı", "🎲 Risk & Haber"])
            
            with t_chart:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="50 Günlük Trend", line=dict(color='orange')))
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

            with t_fund:
                c1, c2, c3 = st.columns(3)
                c1.metric("Ucuzluk (F/K)", f"{fund['FK']:.2f}")
                c2.metric("Defter Değeri (PD/DD)", f"{fund['PDDD']:.2f}")
                c3.metric("Temettü Verimi", f"%{fund['Temettu']:.2f}")
                st.write(f"**Şirket Ünvanı:** {fund['Is_Ismi']}")

            with t_risk:
                st.subheader("Son Haber Başlıkları")
                for n in news:
                    st.write(f"🔹 [{n['title']}]({n['link']})")

if __name__ == "__main__":
    main()
