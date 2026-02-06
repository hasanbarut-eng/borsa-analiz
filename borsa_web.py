import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime
import time

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Hasan Bey Borsa Terminali", layout="wide")
st.title("🛡️ Hasan Bey BİST Karar Destek Terminali")
st.markdown("_Tüm BİST listesinden seçiminizi yapın ve 4'lü teknik süzgeci çalıştırın_")

# --- TÜM BİST LİSTESİ (Genişletilmiş Havuz) ---
@st.cache_data
def get_bist_list():
    # En çok işlem gören ve takip edilen genişletilmiş liste
    hisseler = [
        "ACSEL", "ADEL", "ADESE", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AKBNK", "AKCNS",
        "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "ALARK", "ALBRK", "ALFAS",
        "ALGYO", "ALKA", "ALKIM", "ALVES", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARCLK",
        "ARDYZ", "ARENA", "ARSAN", "ARZUM", "ASCEG", "ASELS", "ASGYO", "ASTOR", "ASUZU", "ATAKP",
        "ATATP", "ATEKS", "AVPGY", "AYDEM", "AYGAZ", "BAGFS", "BANVT", "BARMA", "BERA", "BEYAZ",
        "BIENY", "BIMAS", "BIOEN", "BOBET", "BRISA", "BRKVY", "BRLSM", "BRYAT", "BSOKE", "BTCIM",
        "BUCIM", "BVSAN", "CANTE", "CATES", "CCOLA", "CEMTS", "CIMSA", "CONSE", "CVKMD", "CWENE",
        "DAGHL", "DAPGM", "DARDL", "DENGE", "DERHL", "DESA", "DESPC", "DEVA", "DGNMO", "DOAS",
        "DOCO", "DOHOL", "DOKTA", "DURDO", "DYOBY", "EBEBK", "ECILC", "ECZYT", "EDATA", "EGEEN",
        "EGEPO", "EGGUB", "EGSER", "EKGYO", "ENJSA", "ENKAI", "ERCB", "EREGL", "ERSU", "ESEN",
        "EUPWR", "EUREN", "FENER", "FESL", "FLAP", "FROTO", "GARAN", "GENIL", "GEREL", "GESAN",
        "GIPTA", "GLRYH", "GSDHO", "GUBRF", "GWIND", "HALKB", "HEKTS", "HTTBT", "HUNER", "ICBCT",
        "IDAS", "IDGYO", "IEYHO", "IHEVA", "IHLGM", "IHLAS", "INFO", "INGRM", "INTEM", "INVEO",
        "IPEKE", "ISCTR", "ISDMR", "ISFIN", "ISGYO", "ISMEN", "IZMDC", "IZENR", "KAPLM", "KARDMA",
        "KARDMB", "KARDMD", "KARYE", "KAYSE", "KCAER", "KCHOL", "KENT", "KERVT", "KFEIN", "KLRGY",
        "KMPUR", "KONTR", "KONYA", "KORDS", "KOZAL", "KOZAA", "KRDMD", "KRVGD", "KSTUR", "KUTPO",
        "KZBGY", "LIMAK", "LMKDC", "MAALT", "MAGEN", "MAVI", "MEDTR", "MEGAP", "METUR", "MHRGY",
        "MIATK", "MIPAZ", "MMMTP", "MNDRS", "MNDTR", "MOBTL", "MPARK", "MSGYO", "MTRKS", "MUDO",
        "NETAS", "NIBAS", "NTGAZ", "NTHOL", "NUHCM", "OBAMS", "ODAS", "ONCSH", "ORCA", "ORGE",
        "OTKAR", "OYAKC", "OYYAT", "OZKGY", "OZSUB", "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU",
        "PENTA", "PETKM", "PETUN", "PGSUS", "PINSU", "PKART", "PKENT", "PNLSN", "PNSUT", "POLHO",
        "POLTK", "PRKAB", "PRKME", "PSGYO", "QUAGR", "REEDR", "RNPOL", "RODRG", "RTALB", "RUBNS",
        "SAHOL", "SAMAT", "SANEL", "SANFO", "SANKO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEKFK",
        "SELEC", "SELGD", "SERVE", "SILVR", "SISE", "SKBNK", "SMRTG", "SNGYO", "SNICA", "SNKRN",
        "SOKM", "SONME", "SRVGY", "SUMAS", "SUNTK", "SURGY", "TABGD", "TARKM", "TATGD", "TAVHL",
        "TCELL", "TCOAS", "TEKTU", "TERA", "TETMT", "TGSAS", "THYAO", "TKFEN", "TKNSA", "TMSN",
        "TOASO", "TRCAS", "TRGYO", "TRILC", "TSKB", "TSPOR", "TTKOM", "TTRAK", "TUCLK", "TUPRS",
        "TURSG", "UFUK", "ULAS", "ULKER", "ULUFA", "ULUSE", "UNLU", "USAK", "VAKBN", "VAKFN",
        "VAKKO", "VANGD", "VBTYZ", "VERTU", "VERUS", "VESBE", "VESTL", "VKGYO", "VKING", "YAPRK",
        "YATAS", "YAYLA", "YEOTK", "YESIL", "YGGYO", "YGYO", "YKBNK", "YLTEK", "YNSA", "YYLGD",
        "ZEDUR", "ZOREN", "ZRGYO"
    ]
    return sorted(list(set(hisseler)))

bist_havuz = get_bist_list()

# --- YAN PANEL: SEÇİM MENÜSÜ ---
st.sidebar.header("📋 BİST Filtreleme")
st.sidebar.write("Canlı Derinlik botunda dikkatinizi çeken 10 hisseyi aşağıdan seçin.")

# Çoklu seçim kutusu (Multiselect)
secilenler = st.sidebar.multiselect(
    "Analiz edilecek hisseleri seçin:",
    options=bist_havuz,
    default=["ESEN", "CATES", "SASA", "KAYSE"] # İlk açılışta bunlar hazır gelir
)

# --- ANALİZ MOTORU ---
def profesyonel_analiz(hisse_kod):
    try:
        hisse_full = hisse_kod + ".IS"
        tk = yf.Ticker(hisse_full)
        df = tk.history(period="6mo", interval="1d", timeout=12)
        
        if df.empty or len(df) < 25: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # 4 Kriterli Matematiksel Onay
        df["RSI"] = ta.rsi(df["Close"], length=14)
        macd = ta.macd(df["Close"])
        bb = ta.bbands(df["Close"], length=20, std=2)
        df["SMA20"] = ta.sma(df["Close"], length=20)
        df = pd.concat([df, macd, bb, df[["SMA20"]]], axis=1)
        
        son = df.iloc[-1]
        
        # Puanlama Mantığı (0-4)
        puan = 0
        if son["RSI"] < 45: puan += 1
        if son["MACDh_12_26_9"] > 0: puan += 1
        if son["Close"] < son["BBL_20_2.0"] * 1.05: puan += 1 # Banda yakınlık
        if son["Close"] > son["SMA20"]: puan += 1
        
        return {
            "Hisse": hisse_kod,
            "Fiyat": round(son["Close"], 2),
            "RSI": round(son["RSI"], 1),
            "Puan": f"{puan}/4",
            "Sinyal": "🟢 GÜÇLÜ AL" if puan >= 3 else "🔴 RİSKLİ" if puan <= 1 else "🟡 BEKLE"
        }
    except: return None

# --- ANA EKRAN ---
if st.button("🚀 Seçilen Hisseleri Analiz Et"):
    if not secilenler:
        st.error("⚠️ Lütfen sol taraftaki menüden en az bir hisse seçin.")
    else:
        st.write(f"🔎 **{len(secilenler)}** hisse teknik süzgeçten geçiyor...")
        sonuclar = []
        progress = st.progress(0)
        
        for i, h in enumerate(secilenler):
            res = profesyonel_analiz(h)
            if res: sonuclar.append(res)
            progress.progress((i + 1) / len(secilenler))
            time.sleep(0.1)
        
        if sonuclar:
            df_final = pd.DataFrame(sonuclar)
            st.subheader("📈 Stratejik Onay Tablosu")
            
            # Puanı en yüksek olanı en üste getir ve renklendir
            st.dataframe(df_final.sort_values(by="Puan", ascending=False).style.applymap(
                lambda x: "background-color: #d4edda" if "AL" in str(x) else ("background-color: #f8d7da" if "RİSK" in str(x) else ""),
                subset=["Sinyal"]
            ), use_container_width=True)
            
            # Kartlar
            c1, c2 = st.columns(2)
            try:
                en_iyi = df_final.loc[df_final['Puan'].str[0].astype(int).idxmax()]
                c1.success(f"🌟 En İyi Fırsat: **{en_iyi['Hisse']}** ({en_iyi['Puan']})")
            except: pass
            c2.info(f"🕒 Güncelleme: {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.error("❌ Veri çekilemedi. Yahoo sunucuları şu an cevap vermiyor olabilir.")
else:
    st.info("👈 Sol taraftaki açılır menüden (BİST Listesi) istediğiniz 10 hisseyi seçin.")