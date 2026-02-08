import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. TASARIM VE MOBİL (PWA) KONFİGÜRASYONU
# =================================================================
st.set_page_config(page_title="Borsa Robotu Master V9", layout="wide", page_icon="📈")

# PWA ve Tasarım CSS
st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-title" content="Borsa Robotu">
        <meta name="application-name" content="Borsa Robotu">
        <meta name="apple-mobile-web-app-capable" content="yes">
    </head>
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #0a0c10 !important; border-right: 3px solid #00D4FF; }
        
        /* OKUNURLUK GARANTİSİ */
        section[data-testid="stSidebar"] .stMarkdown p, 
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stSubheader { 
            color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.15rem !important;
            text-shadow: 2px 2px 4px #000000;
        }

        /* KARTLAR VE TABLOLAR */
        .master-card {
            background: #1e293b; padding: 15px; border-radius: 12px; 
            border-left: 6px solid #00D4FF; margin-bottom: 10px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        }
        .yasal-uyari {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #111418; color: #ff4b4b; text-align: center;
            padding: 8px; font-size: 0.85rem; font-weight: bold; border-top: 2px solid #3b82f6; z-index: 999;
        }
        
        /* TRAFİK IŞIKLARI */
        .light { height: 15px; width: 15px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .green { background-color: #00ff00; box-shadow: 0 0 10px #00ff00; }
        .yellow { background-color: #ffff00; box-shadow: 0 0 10px #ffff00; }
        .red { background-color: #ff0000; box-shadow: 0 0 10px #ff0000; }

        /* BUTONLAR */
        .stButton>button {
            background-color: #00D4FF !important; color: #000000 !important;
            font-weight: 900 !important; border-radius: 10px !important; 
            height: 55px !important; width: 100% !important; border: 2px solid white;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. VERİ VE ANALİZ SINIFI
# =================================================================
class AnalystV9:
    def __init__(self, db_name="master_v9_production.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)

    def get_user_space(self, key):
        safe = "".join(filter(str.isalnum, key))
        table = f"u_{safe}"
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return table

    @st.cache_data(ttl=300)
    def run_analysis(_self, symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None, None
            
            # TEKNİK HESAPLAMALAR
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            # RSI
            delta = df['Close'].diff()
            up = delta.where(delta > 0, 0).rolling(14).mean()
            down = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (up / (down + 1e-9))))
            # MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            info = t.info
            fin = {
                "ad": info.get("longName", symbol),
                "cari": info.get("currentRatio", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "fiyat": df['Close'].iloc[-1]
            }
            return df, fin, t.news
        except: return None, None, None

    def get_traffic_lights(self, df):
        # TRAFİK IŞIĞI MANTIĞI
        rsi = df['RSI'].iloc[-1]
        last_price = df['Close'].iloc[-1]
        sma50 = df['SMA50'].iloc[-1]
        macd = df['MACD'].iloc[-1]
        sig = df['Signal'].iloc[-1]

        data = []
        # RSI Işığı
        rsi_status = "green" if 30 < rsi < 60 else ("yellow" if rsi < 30 else "red")
        data.append({"İndikatör": "RSI (14) - Güç", "Değer": f"{rsi:.2f}", "Durum": rsi_status, "Yorum": "30-60 Arası Güvenli"})
        
        # Trend Işığı
        trend_status = "green" if last_price > sma50 else "red"
        data.append({"İndikatör": "SMA 50 - Trend", "Değer": f"{sma50:.2f}", "Durum": trend_status, "Yorum": "Fiyat Üstte ise Pozitif"})
        
        # MACD Işığı
        macd_status = "green" if macd > sig else "red"
        data.append({"İndikatör": "MACD - Momentum", "Değer": "Kesişim", "Durum": macd_status, "Yorum": "Sinyal Üstü Pozitif"})
        
        return data

# =================================================================
# 3. ANA UYGULAMA
# =================================================================
def main():
    av9 = AnalystV9()
    
    st.sidebar.title("🔑 Borsa Kasası")
    key = st.sidebar.text_input("Kişisel Şifre:", type="password")
    
    if not key:
        st.info("👋 Merhaba öğretmenim! Portföyüne ve analizlere ulaşmak için lütfen şifreni gir.")
        return

    ut = av9.get_user_space(key)

    # PORTFÖY GİRİŞİ
    with st.sidebar:
        st.divider()
        st.subheader("➕ Yeni Varlık Ekle")
        s_raw = st.text_input("Hisse (esen, sasa):").upper().strip()
        q_in = st.number_input("Adet", 0.0)
        c_in = st.number_input("Maliyet", 0.0)
        if st.button("KAYDET VE GÜNCELLE"):
            if s_raw:
                symbol = s_raw if s_raw.endswith(".IS") else f"{s_raw}.IS"
                with av9.conn:
                    av9.conn.execute(f"INSERT OR REPLACE INTO {ut} (symbol, qty, cost) VALUES (?,?,?)", (symbol, q_in, c_in))
                st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {ut}", av9.conn)
    if not p_df.empty:
        st.title("🛡️ Borsa Robotu Master V9 Pro")
        active = st.selectbox("İncelemek İstediğiniz Varlık:", ["Seçiniz..."] + p_df['symbol'].tolist())
        
        if active != "Seçiniz...":
            df, fin, news = av9.run_analysis(active)
            if df is not None:
                
                # --- HABERLER ---
                st.subheader(f"📰 {active} Son Dakika Haberleri")
                if news:
                    n_cols = st.columns(3)
                    for i, n in enumerate(news[:3]):
                        with n_cols[i]:
                            st.markdown(f"""<div class="master-card">
                                <a href="{n['link']}" target="_blank" style="text-decoration:none; color:#00D4FF; font-weight:bold;">{n['title'][:55]}...</a>
                                <p style="font-size:0.7rem; color:#94a3b8; margin:0;">{n['publisher']}</p>
                            </div>""", unsafe_allow_html=True)
                
                # --- TRAFİK IŞIKLARI TABLOSU ---
                st.subheader("🚦 Teknik Sinyal Trafik Işıkları")
                lights = av9.get_traffic_lights(df)
                
                # Tablo Başlıkları
                t_cols = st.columns([2, 1, 1, 2])
                t_cols[0].write("**İndikatör**")
                t_cols[1].write("**Değer**")
                t_cols[2].write("**Işık**")
                t_cols[3].write("**Analiz Notu**")
                
                for l in lights:
                    row_cols = st.columns([2, 1, 1, 2])
                    row_cols[0].write(l['İndikatör'])
                    row_cols[1].write(l['Değer'])
                    row_cols[2].markdown(f'<span class="light {l["Durum"]}"></span>', unsafe_allow_html=True)
                    row_cols[3].write(l['Yorum'])
                
                st.divider()

                # --- AI VE GRAFİK ---
                c1, c2 = st.columns([1, 2])
                with c1:
                    y = df['Close'].values[-60:]
                    model = LinearRegression().fit(np.arange(len(y)).reshape(-1,1), y)
                    f_val = model.predict([[len(y)+5]])[0]
                    st.markdown(f"""<div class="master-card">
                        <p style="color:#00D4FF;">🧠 AI TAHMİNİ (5 GÜN)</p>
                        <h2 style="color:white; margin:0;">{fin['fiyat']:.2f} ➔ {f_val:.2f} TL</h2>
                    </div>""", unsafe_allow_html=True)
                    
                    st.markdown(f"""<div class="master-card">
                        <p style="color:#10b981;">🔍 MÜFETTİŞ NOTU</p>
                        <p style="margin:0;">Borç Gücü: {fin['cari']:.2f} | Karlılık: %{fin['oz_kar']:.1f}</p>
                    </div>""", unsafe_allow_html=True)

                with c2:
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold'), name="Trend"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=2, col=1)
                    fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)

                # PORTFÖY METRİKLERİ VE SİLME
                m1, m2, m3 = st.columns([2, 2, 1])
                row = p_df[p_df['symbol'] == active].iloc[0]
                m1.metric("Maliyet", f"{row['cost']:.2f} TL")
                m2.metric("Kâr/Zarar", f"{(fin['fiyat'] - row['cost']) * row['qty']:,.0f} TL", f"{((fin['fiyat']/row['cost'])-1)*100:.2f}%")
                if m3.button("🗑️ HİSSEYİ SİL"):
                    with av9.conn: av9.conn.execute(f"DELETE FROM {ut} WHERE symbol = ?", (active,))
                    st.rerun()

    # SABİT YASAL UYARI
    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR (YTD). Bu sistem verileri matematiksel olarak analiz eder; karar kullanıcıya aittir.</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
