import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
from streamlit_javascript import st_javascript

# --- KONFİGÜRASYON ---
st.set_page_config(page_title="Hasan Bey Terminal v3", layout="wide")

@st.cache_data
def get_bist_list():
    """Tüm BİST Hisse Listesi"""
    return sorted(["A1CAP", "ACSEL", "ADEL", "ADESE", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSGY", "AKSUE", "AKTVY", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALVES", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARCLK", "ARDYZ", "ARENA", "ARSAN", "ARTMS", "ARZUM", "ASCEG", "ASELS", "ASGYO", "ASTOR", "ASUZU", "ATAKP", "ATATP", "ATEKS", "ATLAS", "ATSYH", "AVGYO", "AVHOL", "AVOD", "AVPGY", "AVTUR", "AYCES", "AYDEM", "AYES", "AYGAZ", "AZTEK", "BAGFS", "BAKAB", "BALAT", "BANVT", "BARMA", "BAYRK", "BEBEK", "BERA", "BEYAZ", "BFREN", "BIENY", "BIGCH", "BIMAS", "BINHO", "BIOEN", "BIZIM", "BJKAS", "BLCYT", "BMTKS", "BNASL", "BOBET", "BORLS", "BORSK", "BOSSA", "BRISA", "BRKO", "BRKSN", "BRKVY", "BRLSM", "BRMEN", "BRSAN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "BYDNR", "CANTE", "CARYE", "CATES", "CCOLA", "CELHA", "CEMAS", "CEMTS", "CEOAS", "CIMSA", "CLEBI", "CONSE", "COSMO", "CRDFA", "CREVT", "CRFSA", "CUSAN", "CVKMD", "CWENE", "DAGHL", "DAGI", "DAPGM", "DARDL", "DGATE", "DGGYO", "DGNMO", "DIRIT", "DITAS", "DMSAS", "DOAS", "DOCO", "DOHOL", "DOKTA", "DRYHO", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDATA", "EDIP", "EFORC", "EGEEN", "EGEPO", "EGGUB", "EGLYO", "EGPAY", "EGPRO", "EGSER", "EKGYO", "EKIZ", "EKSUN", "ELITE", "EMKEL", "ENERY", "ENJSA", "ENKAI", "ENTRA", "ERBOS", "ERCB", "EREGL", "ERSU", "ESCOM", "ESEN", "ETILR", "EUPWR", "EUREN", "EYGYO", "FADE", "FENER", "FLAP", "FMIZP", "FONET", "FORMT", "FRIGO", "FROTO", "FZLGY", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN", "GIPTA", "GLBMD", "GLCVY", "GLRYH", "GLYHO", "GMTAS", "GOKNR", "GOLTS", "GOODY", "GOZDE", "GRNYO", "GRSEL", "GSDDE", "GSDHO", "GSRAY", "GUBRF", "GWIND", "GZNMI", "HALKB", "HATEK", "HEDEF", "HEKTS", "HKTM", "HLGYO", "HRKET", "HTTBT", "HUBVC", "HUNER", "HURGZ", "ICBCT", "ICUGS", "IDGYO", "IEYHO", "IHAAS", "IHEVA", "IHLAS", "IHLGM", "IHMAD", "IKLGV", "IMASM", "INDES", "INFO", "INGRM", "INTEM", "INVEO", "IPEKE", "ISATR", "ISBTR", "ISCTR", "ISDMR", "ISFIN", "ISGSY", "ISGYO", "ISMEN", "ISKPL", "ISSEN", "ISYAT", "IZENR", "IZFAS", "IZMDC", "JANTS", "KAPLM", "KAREL", "KARMA", "KARSAN", "KARTN", "KARYE", "KATMR", "KAYSE", "KCAER", "KCHOL", "KFEIN", "KENT", "KERVN", "KERVT", "KGYO", "KIMMR", "KLGYO", "KLRGY", "KLMSN", "KLNMA", "KLSYN", "KMPUR", "KNFRT", "KONTR", "KONYA", "KOPOL", "KORDS", "KOTON", "KOZAL", "KOZAA", "KRONT", "KRSTL", "KRTEK", "KRVGD", "KSTUR", "KTSKR", "KUTPO", "KUZEY", "KZBGY", "KZGYO", "LIDER", "LIDFA", "LIHTP", "LIMAK", "LMKDC", "LOGO", "LUKSK", "MAALT", "MACKO", "MAGEN", "MAKIM", "MAKTK", "MANAS", "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", "MEPET", "MERCN", "MERIT", "METRO", "METUR", "MHRGY", "MIATK", "MIPAZ", "MNDRS", "MNDTR", "MOBTL", "MOGAN", "MPARK", "MRGYO", "MRSHL", "MSGYO", "MTRKS", "MUDO", "MZHLD", "NATEN", "NETAS", "NIBAS", "NTGAZ", "NTHOL", "NUGYO", "NUHCM", "OBAMS", "ODAS", "ONCSH", "ORCA", "ORGE", "ORMA", "OSMEN", "OSTIM", "OTKAR", "OYAKC", "OYAYO", "OYYAT", "OZGYO", "OZKGY", "OZRDN", "OZSUB", "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU", "PATEK", "PCILT", "PEGYO", "PEKGY", "PENTA", "PETKM", "PETUN", "PGSUS", "PINSU", "PKART", "PKENT", "PLTUR", "PNLSN", "PNSUT", "POLHO", "POLTK", "PRKAB", "PRKME", "PRZMA", "PSDTC", "PSGYO", "QNBFB", "QNBFL", "QUAGR", "RALYH", "RAYSG", "REEDR", "RNPOL", "RODRG", "RTALB", "RUBNS", "RYGYO", "RYSAS", "SAHOL", "SAMAT", "SANEL", "SANFO", "SANKO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEGYO", "SEKFK", "SEKUR", "SELEC", "SELGD", "SELVA", "SEYKM", "SILVR", "SISE", "SKBNK", "SKTAS", "SMART", "SMRTG", "SNGYO", "SNICA", "SNKRN", "SNPAM", "SOKM", "SONME", "SRVGY", "SUMAS", "SUNTK", "SURGY", "SUWEN", "TABGD", "TARKM", "TATGD", "TAVHL", "TCELL", "TDGYO", "TEKTU", "TERA", "TETMT", "TGSAS", "THYAO", "TIRE", "TKFEN", "TKNSA", "TLMAN", "TMPOL", "TMSN", "TOASO", "TRCAS", "TRGYO", "TRILC", "TSKB", "TSGYO", "TSPOR", "TTKOM", "TTRAK", "TUCLK", "TUPRS", "TUREX", "TURSG", "UFUK", "ULAS", "ULKER", "ULUFA", "ULUSE", "UNLU", "USAK", "VAKBN", "VAKFN", "VAKKO", "VANGD", "VBTYZ", "VERTU", "VERUS", "VESBE", "VESTL", "VKGYO", "VKING", "YAPRK", "YATAS", "YAYLA", "YEOTK", "YESIL", "YGGYO", "YGYO", "YKBNK", "YLTEK", "YNSA", "YYLGD", "YYAPI", "ZEDUR", "ZOREN", "ZRGYO"])

def profesyonel_analiz_10(symbol):
    """Tam 10 İndikatörlü Motor"""
    try:
        df = yf.download(symbol + ".IS", period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 50: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        c, h, l = df['Close'], df['High'], df['Low']
        
        # HESAPLAMALAR
        diff = c.diff(); g = diff.where(diff > 0, 0).rolling(14).mean(); ls = -diff.where(diff < 0, 0).rolling(14).mean()
        rsi = 100 - (100 / (1 + g/ls))
        e1 = c.ewm(span=12).mean(); e2 = c.ewm(span=26).mean(); macd = e1-e2; sig = macd.ewm(span=9).mean()
        sma20 = c.rolling(20).mean(); sma50 = c.rolling(50).mean(); sma200 = c.rolling(200).mean()
        std = c.rolling(20).std(); bbl = sma20 - (std*2)
        tp = (h+l+c)/3; cci = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean()))
        mf = tp * df['Volume']; pmf = mf.where(tp > tp.shift(1), 0).rolling(14).sum(); nmf = mf.where(tp < tp.shift(1), 0).rolling(14).sum(); mfi = 100 - (100 / (1 + pmf/nmf))
        stok = 100 * (c - l.rolling(14).min()) / (h.rolling(14).max() - l.rolling(14).min())
        mom = (c / c.shift(10)) * 100

        p = sum([rsi.iloc[-1] < 45, (macd-sig).iloc[-1] > 0, c.iloc[-1] > sma20.iloc[-1], c.iloc[-1] < bbl.iloc[-1]*1.05])

        return {
            "Hisse": symbol, "Fiyat": round(c.iloc[-1], 2), "RSI": round(rsi.iloc[-1], 1),
            "MACD": "POZ" if (macd-sig).iloc[-1] > 0 else "NEG", "SMA20": "ÜST" if c.iloc[-1] > sma20.iloc[-1] else "ALT",
            "SMA50": "ÜST" if c.iloc[-1] > sma50.iloc[-1] else "ALT", "SMA200": "ÜST" if c.iloc[-1] > sma200.iloc[-1] else "ALT",
            "CCI": round(cci.iloc[-1], 0), "MFI": round(mfi.iloc[-1], 1), "Stoch": round(stok.iloc[-1], 1),
            "Mom": round(mom.iloc[-1], 1), "Puan": f"{p}/4", "Sinyal": "🟢 AL" if p >= 3 else "🔴 SAT"
        }
    except: return None

def main():
    st.title("🛡️ Hasan Bey BİST Karar Destek Terminali")

    # --- KRİTİK HAFIZA MANTIĞI ---
    # Tarayıcıdan oku (İlk çalışma)
    js_read = st_javascript('localStorage.getItem("hasan_bey_list_v4");')
    
    if 'init' not in st.session_state:
        st.session_state.init = True
        if js_read and js_read != "null":
            st.session_state.current_list = json.loads(js_read)
        else:
            # Buraya ne yazarsanız sayfa ilk kez açıldığında o gelir
            st.session_state.current_list = ["ESEN", "SASA", "THYAO", "AGROT", "REEDR"]

    # --- SIDEBAR ---
    all_symbols = get_bist_list()
    st.sidebar.header("📋 Takip Listeniz")
    
    # Multiselect: default her zaman session_state'den gelir
    secilenler = st.sidebar.multiselect(
        "Hisseleri Seçin:",
        options=all_symbols,
        default=st.session_state.current_list
    )

    if st.sidebar.button("💾 BU LİSTEYİ TARAYICIYA GÖM"):
        # JavaScript ile yerel depoya yaz
        json_data = json.dumps(secilenler)
        st_javascript(f'localStorage.setItem("hasan_bey_list_v4", \'{json_data}\');')
        # Session state'i güncelle
        st.session_state.current_list = secilenler
        st.sidebar.success("✅ Liste tarayıcıya yazıldı! Lütfen sayfayı yenileyin.")
        # Sayfayı zorla yenileyerek JavaScript'in Python'a veriyi vermesini sağlıyoruz
        st.rerun()

    # --- ANALİZ ---
    if st.button(f"🚀 {len(secilenler)} Hisseyi Analiz Et"):
        if not secilenler: st.warning("Hisse seçin."); return
        results = []
        bar = st.progress(0); status = st.empty()
        for i, s in enumerate(secilenler):
            status.text(f"Analiz ediliyor: {s}")
            res = profesyonel_analiz_10(s)
            if res: results.append(res)
            bar.progress((i+1)/len(secilenler))
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df.sort_values("Puan", ascending=False), use_container_width=True)
        status.empty(); bar.empty()

if __name__ == "__main__":
    main()
