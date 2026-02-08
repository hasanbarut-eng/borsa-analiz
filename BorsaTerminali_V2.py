import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
import sqlite3

# =================================================================
# 1. DATABASE (GÜVENLİ HAFIZA - VERİ TABANI)
# =================================================================
class TerminalDB:
    def __init__(self, db_name="komuta_merkezi_final_v5.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        with self.conn:
            self.conn.execute("""CREATE TABLE IF NOT EXISTS portfolio 
                (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)""")

    def save_p(self, s, q, c, t, stop):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO portfolio VALUES (?,?,?,?,?)", (s, q, c, t, stop))

    def get_p(self):
        return pd.read_sql_query("SELECT * FROM portfolio", self.conn)

    def delete_p(self, s):
        with self.conn:
            self.conn.execute("DELETE FROM portfolio WHERE symbol = ?", (s,))

# =================================================================
# 2. ANALİZ MOTORU (ZEKA KATMANI)
# =================================================================
class AnalystEngine:
    @staticmethod
    def get_full_analysis(symbol):
        try:
            df = yf.download(symbol, period="2y", interval="1d", progress=False)
            if df.empty: return None, None, None
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            df['SMA_50'] = df['Close'].rolling(50).mean()
            delta = df['Close'].diff()
            g = delta.where(delta > 0, 0).rolling(14).mean()
            l = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g / l)))

            t = yf.Ticker(symbol)
            info = t.info
            fund = {
                "FK": info.get('trailingPE', 0),
                "PDDD": info.get('priceToBook', 0),
                "Temettu": info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                "Is_Ismi": info.get('longName', symbol)
            }
            return df, fund, t.news[:5]
        except Exception:
            return None, None, None

    @staticmethod
    def generate_simple_decision(df, fund):
        last_c = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        sma50 = float(df['SMA_50'].iloc[-1])
        
        score = 0
        reasons = []
        if last_c > sma50:
            score += 2; reasons.append("✅ TREND: YUKARI (Güçlü duruş)")
        else:
            score -= 1; reasons.append("⚠️ TREND: ZAYIF (Baskı var)")

        if rsi < 35:
            score += 2; reasons.append("🟢 ALIM İŞTAHI: ÇOK UCUZ (Fırsat bölgesi)")
        elif rsi > 75:
            score -= 2; reasons.append("🔴 ALIM İŞTAHI: DOYUMDA (Dikkatli ol)")

        if fund['FK'] != 0 and fund['FK'] < 15:
            score += 1; reasons.append(f"💎 TEMEL YAPI: UCUZ (F/K: {fund['FK']:.1f})")

        if score >= 3: d, color, t_color = "GÜÇLÜ AL", "#00FF00", "#000000"
        elif 1 <= score < 3: d, color, t_color = "OLUMLU / TUT", "#00D4FF", "#000000"
        elif -1 <= score < 1: d, color, t_color = "NÖTR / BEKLE", "#FFFF00", "#000000"
        else: d, color, t_color = "RİSKLİ / SAT", "#FF0000", "#FFFFFF"
        return d, reasons, color, t_color

# =================================================================
# 3. GÖRSEL TASARIM (MAKSİMUM OKUNABİLİRLİK)
# =================================================================
def main():
    st.set_page_config(page_title="Pro-Terminal Final V2", layout="wide")
    db = TerminalDB()
    ae = AnalystEngine()

    # OKUNABİLİRLİK İÇİN ÖZEL CSS (KRİSTAL NETLİĞİ)
    st.markdown("""<style>
        .stApp { background-color: #0E1117; }
        
        /* SIDEBAR (SOL PANEL) TASARIMI */
        section[data-testid="stSidebar"] {
            background-color: #111418 !important;
            border-right: 1px solid #2d333b;
        }
        
        /* TÜM BAŞLIKLAR VE ETİKETLER - SAF BEYAZ VE KALIN */
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] div {
            color: #FFFFFF !important;
            font-weight: 900 !important;
            font-size: 1.1rem !important;
            opacity: 1 !important;
        }

        /* GİRİŞ KUTULARI - SİYAH YAZI, BEYAZ ZEMİN */
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
            color: #000000 !important;
            background-color: #FFFFFF !important;
            font-weight: bold !important;
            border-radius: 8px !important;
            border: 2px solid #00D4FF !important;
        }

        /* ANA BUTON TASARIMI */
        div.stButton > button:first-child {
            background-color: #00D4FF !important;
            color: #000000 !important;
            font-weight: 900 !important;
            height: 55px !important;
            border: 2px solid #FFFFFF !important;
            box-shadow: 0px 4px 15px rgba(0, 212, 255, 0.3) !important;
        }

        /* SİLME BUTONU (ÇÖP KUTUSU) DÜZENLEME */
        div[data-testid="column"] button {
            background-color: #1c2128 !important;
            border: 1px solid #ff4b4b !important;
            color: #ff4b4b !important;
        }

        /* METRİKLER VE GENEL METİNLER */
        [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: bold !important; }
        .decision-card { padding: 30px; border-radius: 20px; border: 4px solid #FFFFFF; }
        p, li, span { color: #FFFFFF !important; }
    </style>""", unsafe_allow_html=True)

    st.title("🛡️ Borsa Stratejik Karar Terminali")

    with st.sidebar:
        st.header("💼 Portföy & Alarm")
        raw_s = st.text_input("Hisse Kodu (Örn: ESEN)", value="THYAO").upper().strip()
        s_in = raw_s + ".IS" if raw_s and not raw_s.endswith(".IS") else raw_s
        
        q_in = st.number_input("Adet", min_value=0.0, step=1.0)
        c_in = st.number_input("Maliyet (TL)", min_value=0.0, step=0.01)
        
        st.write("---")
        st.subheader("🔔 Fiyat Alarmları") # ARTIK NET OKUNACAK
        target_in = st.number_input("Hedef Fiyat (Üst)", min_value=0.0, step=0.1)
        stop_in = st.number_input("Stop Fiyat (Alt)", min_value=0.0, step=0.1)
        
        if st.button("KAYDET VE ANALİZ ET"):
            db.save_p(s_in, q_in, c_in, target_in, stop_in)
            st.rerun()
        
        st.write("---")
        st.subheader("📋 İzleme Listesi")
        p_df = db.get_p()
        if not p_df.empty:
            for s in p_df['symbol']:
                col_a, col_b = st.columns([4, 1.2])
                with col_b:
                    if st.button("🗑️", key=f"del_{s}"):
                        db.delete_p(s); st.rerun()
                with col_a:
                    st.info(f"**{s}**")

    # PORTFÖY ÖZETİ
    if not p_df.empty:
        st.subheader("📊 Canlı Takip Paneli")
        total_v, total_p = 0.0, 0.0
        cols = st.columns(len(p_df))
        
        for i, row in p_df.iterrows():
            live = yf.download(row['symbol'], period="2d", progress=False)
            if not live.empty:
                curr = float(live['Close'].iloc[-1])
                pnl = (curr - row['cost']) * row['qty']
                total_v += (curr * row['qty']); total_p += pnl
                with cols[i]:
                    st.metric(row['symbol'], f"{curr:.2f} TL", f"{pnl:,.0f} TL")
                    if row['target'] > 0 and curr >= row['target']:
                        st.success("🎯 HEDEF GÖRÜLDÜ!")
                    elif row['stop'] > 0 and curr <= row['stop']:
                        st.error("⚠️ STOP SEVİYESİ!")
        
        st.warning(f"💰 **Toplam Değer:** {total_v:,.2f} TL | **Toplam Kar/Zarar:** {total_p:,.2f} TL")

    st.divider()
    active_s = st.selectbox("Detaylı Analiz", options=p_df['symbol'].tolist() if not p_df.empty else ["THYAO.IS"])
    
    if active_s:
        df, fund, news = ae.get_full_analysis(active_s)
        if df is not None:
            dec, reasons, color, t_color = ae.generate_simple_decision(df, fund)
            st.markdown(f"""<div class="decision-card" style="background-color: {color};">
                <h1 style="color: {t_color} !important; margin: 0; font-size: 2.2rem;">SİSTEM KARARI: {dec}</h1>
                <hr style="border: 1px solid {t_color};">
                <ul style="list-style-type: none; padding: 0;">
                    {''.join([f"<li style='color: {t_color} !important; font-size: 1.4rem; font-weight: bold;'>{r}</li>" for r in reasons])}
                </ul>
            </div>""", unsafe_allow_html=True)

            t_chart, t_fund, t_risk = st.tabs(["📈 Grafik", "🏢 Temel Veriler", "📰 Haberler"])
            with t_chart:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="Trend", line=dict(color='#FFD700', width=3)))
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

            with t_fund:
                c1, c2, c3 = st.columns(3)
                c1.metric("F/K Oranı", f"{fund['FK']:.2f}")
                c2.metric("PD/DD Oranı", f"{fund['PDDD']:.2f}")
                c3.metric("Temettü Verimi", f"%{fund['Temettu']:.2f}")
                st.info(f"🏢 **Resmi Adı:** {fund['Is_Ismi']}")

            with t_risk:
                if news:
                    for n in news:
                        st.markdown(f"🔹 **[{n.get('title', 'Haber')}]({n.get('link', '#')})**")
                else: st.write("Haber bulunamadı.")

if __name__ == "__main__":
    main()
