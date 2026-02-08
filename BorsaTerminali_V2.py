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
st.set_page_config(page_title="Borsa Robotu Master V10", layout="wide", page_icon="📈")

st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-title" content="Borsa Robotu">
        <meta name="application-name" content="Borsa Robotu">
        <meta name="apple-mobile-web-app-capable" content="yes">
    </head>
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #0a0c10 !important; border-right: 3px solid #00D4FF; }
        
        /* OKUNURLUK: KAR BEYAZI VE NET */
        section[data-testid="stSidebar"] .stMarkdown p, 
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stSubheader { 
            color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.15rem !important;
            text-shadow: 2px 2px 4px #000000;
        }

        /* ANALİZ KARTLARI */
        .master-card {
            background: #1e293b; padding: 20px; border-radius: 12px; 
            border-left: 8px solid #00D4FF; margin-bottom: 15px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }
        .master-card h3, .master-card p, .master-card li {
            color: #FFFFFF !important; font-weight: 600 !important;
        }
        
        /* TRAFİK IŞIKLARI */
        .light { height: 16px; width: 16px; border-radius: 50%; display: inline-block; margin-right: 8px; border: 1px solid white; }
        .green { background-color: #00ff00; box-shadow: 0 0 12px #00ff00; }
        .yellow { background-color: #ffff00; box-shadow: 0 0 12px #ffff00; }
        .red { background-color: #ff0000; box-shadow: 0 0 12px #ff0000; }

        .stButton>button {
            background-color: #00D4FF !important; color: #000000 !important;
            font-weight: 900 !important; border-radius: 10px !important; 
            height: 60px !important; width: 100% !important; border: 3px solid white;
        }
        
        .yasal-uyari {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #111418; color: #ff4b4b; text-align: center;
            padding: 8px; font-size: 0.85rem; font-weight: bold; border-top: 2px solid #3b82f6; z-index: 999;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. VERİ VE GİZLİLİK MİMARİSİ
# =================================================================
class MasterSystemV10:
    def __init__(self, db_name="master_v10_pro_ultimate.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)

    def get_user_table(self, key):
        safe = "".join(filter(str.isalnum, key))
        table = f"u_{safe}"
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return table

    @st.cache_data(ttl=300)
    def fetch_comprehensive_data(_self, symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None, None
            
            # Teknikler
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            df['MB'] = df['Close'].rolling(20).mean()
            df['UB'] = df['MB'] + (df['Close'].rolling(20).std() * 2)
            df['LB'] = df['MB'] - (df['Close'].rolling(20).std() * 2)
            delta = df['Close'].diff()
            up = delta.where(delta > 0, 0).rolling(14).mean()
            down = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (up / (down + 1e-9))))
            
            # Bilanço ve Temel Detaylar
            info = t.info
            fin = {
                "ad": info.get("longName", symbol),
                "sektor": info.get("sector", "Bilinmiyor"),
                "ozet": info.get("longBusinessSummary", "Bilgi yok."),
                "cari": info.get("currentRatio", 0),
                "likidite": info.get("quickRatio", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "fk": info.get("trailingPE", "N/A"),
                "pddd": info.get("priceToBook", "N/A"),
                "eps": info.get("trailingEps", "N/A"),
                "borc_oran": info.get("debtToEquity", 0),
                "fiyat": df['Close'].iloc[-1]
            }
            return df, fin, t.news
        except: return None, None, None

# =================================================================
# 3. ANA PROGRAM
# =================================================================
def main():
    sys = MasterSystemV10()
    
    st.sidebar.title("🔑 Borsa Kasası")
    key = st.sidebar.text_input("Şifrenizi Girin:", type="password")
    
    if not key:
        st.info("👋 Hoş geldin öğretmenim! Şifrenizi girerek tüm motorları aktif edebilirsiniz.")
        return

    table = sys.get_user_table(key)

    with st.sidebar:
        st.divider()
        st.subheader("➕ Portföy Yönetimi")
        s_raw = st.text_input("Hisse Kodu:").upper().strip()
        q_in = st.number_input("Adet", 0.0)
        c_in = st.number_input("Maliyet", 0.0)
        t_in = st.number_input("Hedef", 0.0)
        st_in = st.number_input("Stop", 0.0)
        
        if st.button("KAYDET VE ANALİZ ET"):
            if s_raw:
                symbol = s_raw if s_raw.endswith(".IS") else f"{s_raw}.IS"
                with sys.conn:
                    sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?)", (symbol, q_in, c_in, t_in, st_in))
                st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        st.title("🛡️ Borsa Robotu Master V10 Ultimate")
        active = st.selectbox("İncelemek İstediğiniz Varlık:", ["Seçiniz..."] + p_df['symbol'].tolist())
        
        if active != "Seçiniz...":
            df, fin, news = sys.fetch_comprehensive_data(active)
            if df is not None:
                
                # --- HABERLER ---
                st.subheader(f"📰 {active} Haber Akışı")
                if news:
                    n_cols = st.columns(3)
                    for i, n in enumerate(news[:3]):
                        with n_cols[i]:
                            st.markdown(f"""<div class="master-card"><a href="{n['link']}" target="_blank" style="text-decoration:none; color:#00D4FF; font-weight:bold;">{n['title'][:60]}...</a></div>""", unsafe_allow_html=True)
                
                # --- DERİN BİLANÇO VE TEMEL ANALİZ ---
                st.subheader("📊 Derin Temel Analiz ve Bilanço Karnesi")
                c_ta, c_ba = st.columns([1, 1])
                
                with c_ta:
                    st.markdown(f"""<div class="master-card">
                        <h3 style="color:#00D4FF;">🏢 Şirket ve Temel Veriler</h3>
                        <p><b>Sektör:</b> {fin['sektor']}</p>
                        <p><b>F/K (Fiyat/Kazanç):</b> {fin['fk']}</p>
                        <p><b>PD/DD:</b> {fin['pddd']}</p>
                        <p><b>Hisse Başı Kar (EPS):</b> {fin['eps']}</p>
                        <hr>
                        <p style="font-size:0.85rem;">{fin['ozet'][:300]}...</p>
                    </div>""", unsafe_allow_html=True)

                with c_ba:
                    c_status = "🟢" if fin['cari'] > 1.5 else "🔴"
                    k_status = "🟢" if fin['oz_kar'] > 20 else "🟡"
                    st.markdown(f"""<div class="master-card">
                        <h3 style="color:#10b981;">🔍 Bilanço Müfettiş Raporu</h3>
                        <p>{c_status} <b>Borç Ödeme Kapasitesi:</b> Cari oran {fin['cari']:.2f}. { 'Şirketin nakit gücü çok yüksek, borçlarını kolayca öder.' if fin['cari']>1.5 else 'Kısa vadeli borç yükü izlenmelidir.' }</p>
                        <p>{k_status} <b>Karlılık Verimi:</b> Özsermaye karlılığı %{fin['oz_kar']:.1f}. { 'Şirket sermayesini mükemmel bir verimle kâra dönüştürüyor.' if fin['oz_kar']>20 else 'Karlılık sektör ortalamalarında seyrediyor.' }</p>
                        <p>⚖️ <b>Borç/Özkaynak:</b> {fin['borc_oran']:.2f}. Borçluluk yapısı dengeli.</p>
                    </div>""", unsafe_allow_html=True)

                # --- TRAFİK IŞIKLARI ---
                st.subheader("🚦 Teknik Sinyal Trafik Işıkları")
                rsi_val = df['RSI'].iloc[-1]
                rsi_c = "green" if 35 < rsi_val < 65 else "yellow"
                sma_val = df['SMA50'].iloc[-1]
                sma_c = "green" if fin['fiyat'] > sma_val else "red"
                
                tr_cols = st.columns(2)
                tr_cols[0].markdown(f'<div class="master-card"><span class="light {rsi_c}"></span> <b>RSI:</b> {rsi_val:.2f} (Güçlü Durum)</div>', unsafe_allow_html=True)
                tr_cols[1].markdown(f'<div class="master-card"><span class="light {sma_c}"></span> <b>Trend:</b> { "Trend Üstü (Pozitif)" if sma_c=="green" else "Trend Altı (Negatif)" }</div>', unsafe_allow_html=True)

                # --- AI VE GRAFİK ---
                st.divider()
                y = df['Close'].values[-60:]
                model = LinearRegression().fit(np.arange(len(y)).reshape(-1,1), y)
                f_val = model.predict([[len(y)+5]])[0]
                
                st.markdown(f"""<div class="master-card" style="border-color:#00D4FF; text-align:center;">
                    <h3 style="margin:0;">🧠 AI TAHMİNİ (5 GÜN): {fin['fiyat']:.2f} ➔ {f_val:.2f} TL</h3>
                </div>""", unsafe_allow_html=True)

                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['UB'], line=dict(color='rgba(255,255,255,0.2)'), name="Bollinger"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold'), name="SMA50"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=2, col=1)
                fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                # --- METRİKLER VE ALARMLAR ---
                m1, m2, m3 = st.columns([2, 2, 1])
                row = p_df[p_df['symbol'] == active].iloc[0]
                m1.metric("Anlık", f"{fin['fiyat']:.2f} TL")
                m2.metric("Kâr/Zarar", f"{(fin['fiyat'] - row['cost']) * row['qty']:,.0f} TL")
                if m3.button("🗑️ HİSSEYİ SİL"):
                    with sys.conn: sys.conn.execute(f"DELETE FROM {table} WHERE symbol = ?", (active,))
                    st.rerun()
                
                if row['target'] > 0 and fin['fiyat'] >= row['target']:
                    st.balloons(); st.success(f"🎯 HEDEF FİYAT ({row['target']} TL) GÖRÜLDÜ!")
                elif row['stop'] > 0 and fin['fiyat'] <= row['stop']:
                    st.error(f"⚠️ STOP SEVİYESİ ({row['stop']} TL) GÖRÜLDÜ!")

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR (YTD).</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
