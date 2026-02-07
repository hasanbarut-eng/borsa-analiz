import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# --- AYARLAR ---
TOKEN = "8255121421:AAG1biq7jrgLFAbWmzOFs6D4wsPzoDUjYeM"
CHAT_ID = "8479457745"

# TAM LİSTE (140+ HİSSE)
hisse_listesi = [
    "ESEN", "CATES", "KAYSE", "AGROT", "ALVES", "REEDR", "MIATK", "EUPWR", "ASTOR", "SASA",
    "THYAO", "ASELS", "EREGL", "AKBNK", "GARAN", "SISE", "KCHOL", "BIMAS", "TUPRS", "ISCTR",
    "EKGYO", "KARDMD", "PETKM", "ARCLK", "PGSUS", "KOZAL", "TCELL", "FROTO", "TOASO", "ENJSA",
    "GUBRF", "KONTR", "YEOTK", "SMRTG", "ALARK", "ODAS", "DOAS", "KCAER", "VAKBN", "HALKB",
    "ISMEN", "SAHOL", "YKBNK", "MGROS", "VESTL", "DOCO", "EGEEN", "TAVHL", "TKFEN", "ADESE",
    "AEFES", "AFYON", "AGESA", "AGHOL", "AKCNS", "AKENR", "AKFGY", "AKFYE", "ALBRK", "ALFAS",
    "ALGYO", "ALKA", "ALKIM", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARZUM", "ASGYO",
    "ASUZU", "ATAKP", "ATEKS", "AVPGY", "AYDEM", "AYGAZ", "BAGFS", "BANVT", "BERA", "BIENY",
    "BRLSM", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BVSAN", "CANTE", "CCOLA", "CEMTS", "CIMSA",
    "CWENE", "EBEBK", "ECILC", "ECZYT", "EGGUB", "ENKAI", "EUREN", "FENER", "GENIL", "GESAN",
    "GSDHO", "GWIND", "INVEO", "IPEKE", "ISDMR", "IZMDC", "KARSN", "KENT", "KERVT", "KLRGY",
    "KMPUR", "KONYA", "KORDS", "KOZAA", "LOGO", "MPARK", "NETAS", "OTKAR", "OYAKC", "QUAGR",
    "SKBNK", "SNGYO", "TTKOM", "TTRAK", "ULKER", "VESBE", "ZOREN", "MAGEN", "FORMT", "HUNER",
    "ALFAS", "BRSAN", "SDTTR", "KOPOL", "SAYAS", "GLYHO", "TSKB", "DOAS", "BOBET", " ENERY",
    "TATEN", "IZENR", "CVMEK", "EFORC", "KUZEY", "MHRGY", "REEDR", "TABGD", "HRKET", " PATE"
]

hisseler = [h + ".IS" for h in sorted(list(set(hisse_listesi)))]

def rsi_hesapla(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

sonuclar = []

print(f"📡 {len(hisseler)} Hisse taranıyor...")

for h in hisseler:
    try:
        data = yf.download(h, period="6mo", interval="1d", auto_adjust=True, progress=False, timeout=15)
        if data.empty or len(data) < 30: continue
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

        # GÖSTERGELER
        rsi_son = rsi_hesapla(data["Close"]).iloc[-1]
        fiyat_son = data["Close"].iloc[-1]
        sma20_son = data["Close"].rolling(20).mean().iloc[-1]
        hacim_ort = data["Volume"].rolling(10).mean().iloc[-1]
        hacim_son = data["Volume"].iloc[-1]

        # PUANLAMA MANTIĞI
        puan = 0
        r_metin = "UYGUN" if 30 < rsi_son < 65 else "ZAYIF"
        s_metin = "YUKARI" if fiyat_son > sma20_son else "ASAGI"
        h_metin = "GUCLU" if hacim_son > hacim_ort else "DUSUK"
        
        if r_metin == "UYGUN": puan += 1
        if s_metin == "YUKARI": puan += 1
        if h_metin == "GUCLU": puan += 1

        # FİLTRE: SADECE EN İYİLER (2-3) VE EN KÖTÜLER (0)
        if puan in [0, 2, 3]:
            sonuclar.append({
                "Kod": h.replace(".IS", ""),
                "Fiyat": f"{fiyat_son:.2f}",
                "RSI": f"{rsi_son:.1f} ({r_metin})",
                "SMA20": s_metin,
                "Hacim": h_metin,
                "Skor": puan
            })
        time.sleep(0.1)
    except: continue

# --- WEB GÖRÜNTÜSÜ (KESKİN RENKLER VE BAŞLIKLAR) ---
html = f"""
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8">
<style>
    body {{ background: #000; color: #fff; font-family: sans-serif; }}
    table {{ width: 95%; margin: 20px auto; border-collapse: collapse; }}
    th {{ background: #1a1a1a; color: #00d2ff; padding: 15px; border: 2px solid #333; }}
    td {{ padding: 12px; border: 1px solid #333; font-weight: bold; text-align: center; }}
    .yesil {{ background-color: #054d1a; color: #90ee90; }} /* EN İYİLER */
    .kirmizi {{ background-color: #5a0505; color: #ffcccb; }} /* EN KÖTÜLER */
</style>
</head>
<body>
    <h2 align="center">🎯 HASAN BEY 140+ HİSSE ANALİZ TABLOSU</h2>
    <p align="center">Sadece En İyiler (2-3 Puan) ve En Kötüler (0 Puan) listelenmiştir.</p>
    <table>
        <tr>
            <th>HİSSE</th>
            <th>FİYAT</th>
            <th>RSI (30-65 ARASI)</th>
            <th>SMA20 (TREND YÖNÜ)</th>
            <th>HACİM (GÜÇ GÖSTERGESİ)</th>
            <th>PUAN (MAX 3)</th>
        </tr>
"""
for s in sorted(sonuclar, key=lambda x: -x['Skor']):
    cls = "yesil" if s['Skor'] >= 2 else "kirmizi"
