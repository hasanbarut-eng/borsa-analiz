import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. TASARIM VE KRİSTAL OKUNURLUK (PRODUCTION LEVEL)
# =================================================================
st.set_page_config(page_title="Borsa Robotu Master V7 Pro", layout="wide", page_icon="🏦")

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #111418 !important; border-right: 2px solid #00D4FF; }
        
        /* BİLANÇO KARAR KARTLARI */
        .status-card {
            padding: 20px; border-radius: 15px; margin-bottom: 15px; border-left: 10px solid;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
        }
        .olumlu { background-color: #064e3b; border-color: #10b981; color: #ecfdf5; }
        .olumsuz { background-color: #7f1d1d; border-color: #ef4444; color: #fef2f2; }
        .notur { background-color: #334155; border-color: #94a3b8; color: #f1f5f9; }

        /* DEV KAYDET BUTONU */
        .stButton>button {
            background-color: #00D4FF !important; color: #000000 !important;
            font-weight: 900 !important; border-radius: 12px !important; 
            height: 60px !important; width: 100% !important;
            border: 2px solid #FFFFFF !important; font-size: 1.2rem !important;
        }
        
        /* OKUNUR METİNLER */
        .card-desc { font-size: 1rem; font-weight: 500; line-height: 1.4; }
        label, p { color: white !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. HIZLI VERİ VE PORTFÖY YÖNETİMİ
# =================================================================
class ProductionStorage:
    def __init__(self, db_name="master_portfoy_v7.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        # Genel portföy yapısı
        pass

    def get_user_table(self, key):
        safe_key = "".join(filter(str.isalnum, key))
        table_name = f"u_{safe_key}"
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return table_name

    def save_stock(self, table, s, q, c, t, stp):
        with self.conn:
            self.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?)", (s, q, c, t, stp))

    def get_portfolio(self, table):
        try: return pd.read_sql_query(f"SELECT * FROM {table}", self.conn)
        except: return pd.DataFrame()

    def remove_stock(self, table, s):
        with self.conn: self.conn.execute(f"DELETE FROM {table} WHERE symbol = ?", (s,))

# =================================================================
# 3. MÜFETTİŞ ANALİZ MOTORU (HIZLANDIRILMIŞ)
# =================================================================
class StockInspector:
    @staticmethod
    @st.cache_data(ttl=300) # 5 Dakika boyunca veriyi hafızada tutar, hızı 10 kat artırır.
    def get_comprehensive_data(symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None, None
            
            # Teknik Hesaplamalar
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            # RSI
            delta = df['Close'].diff()
            g = delta.where(delta > 0, 0).rolling(14).mean()
            l = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g / (l + 1e-9))))
            
            info = t.info
            # Bilanço Müfettişi Verileri
            fin_report = {
                "ad": info.get("longName", "Bilinmiyor"),
                "net_kar": info.get("netIncomeToCommon", 0),
                "cari_oran": info.get("currentRatio", 0),
                "ozsermaye_kar": info.get("returnOnEquity", 0) * 100,
                "fk": info.get("trailingPE", "N/A"),
                "pddd": info.get("priceToBook", "N/A"),
                "borc_ozkaynak": info.get("debtToEquity", 0)
            }
            return df, fin_report, t
        except: return None, None, None

    @staticmethod
    def judge_balance_sheet(fin):
        score = 0
        reasons = []
        
        # Kar/Zarar Kontrolü
        if fin['net_kar'] > 0:
            score += 1
            reasons.append(f"✅ Şirket son dönemde {fin['net_kar']/1e6:.1f} Milyon TL kâr açıkladı.")
        else:
            score -= 1
            reasons.append("❌ Şirket son dönemde zarar açıkladı, nakit akışı riskli.")

        # Borç Ödeme Gücü (Cari Oran)
        if fin['cari_oran'] > 1.5:
            score += 1
            reasons.append(f"✅ Cari Oran {fin['cari_oran']:.2f}: Borç ödeme gücü çok yüksek.")
        elif fin['cari_oran'] < 1:
            score -= 1
            reasons.append(f"❌ Cari Oran {fin['cari_oran']:.2f}: Kısa vadeli borçlar risk yaratabilir.")

        # Verimlilik
        if fin['ozsermaye_kar'] > 25:
            score += 1
            reasons.append(f"✅ Özsermaye Karlılığı %{fin['oz_kar']:.1f}: Müthiş verimlilik.")
        
        # Karar Mekanizması
        if score >= 2: return "olumlu", "OLUMLU", reasons
        elif score <= -1: return "olumsuz", "OLUMSUZ", reasons
        else: return "notur", "NÖTR / İZLEMEDE", reasons

# =================================================================
# 4. ANA EKRAN
# =================================================================
def main():
    db = ProductionStorage()
    insp = StockInspector()

    st.sidebar.title("🔑 Portföy Anahtarı")
    key = st.sidebar.text_input("Şifrenizi Girin:", type="password", help="Hisseleriniz bu şifre altında saklanır.")
    
    if not key:
        st.info("👋 Hoş geldin öğretmenim! Portföyünü oluşturmak veya görmek için lütfen şifreni gir.")
        return

    table = db.get_user_table(key)

    # --- HİSSE EKLEME FORMU ---
    st.sidebar.divider()
    st.sidebar.subheader("➕ Yeni Hisse Ekle")
    raw_s = st.sidebar.text_input("Hisse Kodu (Örn: esen, thyao):").strip().upper()
    q_in = st.sidebar.number_input("Adet", min_value=0.0, step=1.0)
    c_in = st.sidebar.number_input("Maliyet (TL)", min_value=0.0)
    t_in = st.sidebar.number_input("Hedef Satış", min_value=0.0)
    st_in = st.sidebar.number_input("Stop Loss", min_value=0.0)
    
    if st.sidebar.button("PORTFÖYE EKLE"):
        if raw_s:
            s_code = raw_s if raw_s.endswith(".IS") else f"{raw_s}.IS"
            db.save_stock(table, s_code, q_in, c_in, t_in, st_in)
            st.rerun()

    # --- PORTFÖY GÖRÜNÜMÜ ---
    port_df = db.get_portfolio(table)
    
    if not port_df.empty:
        st.title("🛡️ Master Portföy ve Müfettiş Analizi")
        selected_stock = st.selectbox("Analiz Edilecek Hisseni Seç:", port_df['symbol'].tolist())
        
        df, fin, t_obj = insp.get_comprehensive_data(selected_stock)
        
        if df is not None:
            class_name, label, reasons = insp.judge_balance_sheet(fin)
            
            # --- 1. MÜFETTİŞ KARARI VE AI ---
            col_ai, col_fin = st.columns(2)
            
            with col_ai:
                # AI Projeksiyon (Hızlı Linear Regression)
                y = df['Close'].values[-60:]
                x = np.arange(len(y)).reshape(-1, 1)
                model = LinearRegression().fit(x, y)
                future_val = model.predict([[len(y)+5]])[0]
                
                st.markdown(f"""<div class="status-card notur">
                    <p class="card-title">🧠 AI YOL HARİTASI (5 GÜN)</p>
                    <h1 style="color:white; margin:0;">{df['Close'].iloc[-1]:.2f} ➔ {future_val:.2f} TL</h1>
                    <p style="margin:0; opacity:0.8;">Trend yönü doğrusal olarak hesaplandı.</p>
                </div>""", unsafe_allow_html=True)

            with col_fin:
                st.markdown(f"""<div class="status-card {class_name}">
                    <p class="card-title">🔍 BİLANÇO MÜFETTİŞİ: {label}</p>
                    <div class="card-desc">{'<br>'.join(reasons)}</div>
                </div>""", unsafe_allow_html=True)

            # --- 2. TEKNİK GRAFİK ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=('Fiyat ve Trendler', 'RSI Güç'), row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Mum"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold'), name="SMA50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=2, col=1)
            fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- 3. PORTFÖY DURUMU VE SİLME ---
            m1, m2, m3 = st.columns([2, 2, 1])
            curr_price = df['Close'].iloc[-1]
            row = port_df[port_df['symbol'] == selected_stock].iloc[0]
            
            m1.metric("Anlık", f"{curr_price:.2f} TL")
            net_kz = (curr_price - row['cost']) * row['qty']
            m2.metric("Kâr/Zarar", f"{net_kz:,.0f} TL", f"{((curr_price/row['cost'])-1)*100:.2f}%")
            
            if m3.button("🗑️ BU HİSSEYİ SİL"):
                db.remove_stock(table, selected_stock); st.rerun()

    else:
        st.warning("👈 Portföyün henüz boş. Sol taraftan şifreni gir ve hisselerini eklemeye baş!")

if __name__ == "__main__":
    main()
