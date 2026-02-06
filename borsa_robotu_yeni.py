import requests
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import time
import logging
import sys

# --- LOGGING YAPILANDIRMASI ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])

class YeniBorsaSistemi:
    def __init__(self):
        # Hasan Bey Özel Ayarlar
        self.TOKEN = "8255121421:AAG1biq7jrgLFAbWmzOFs6D4wsPzoDUjYeM"
        self.CHAT_ID = "8479457745"
        
        # 1. GRUP: HASAN BEY FAVORİLER (Her zaman en üstte)
        self.favoriler = [
            "ESEN", "CATES", "KAYSE", "AGROT", "ALVES", "REEDR", "MIATK", "EUPWR", "ASTOR", "SASA",
            "KAYSE", "CATES", "AGROT", "ALVES", "REEDR"
        ]
        
        # 2. GRUP: GENİŞ HAVUZ (100+ HİSSE)
        self.ek_liste = [
            "THYAO", "ASELS", "EREGL", "AKBNK", "GARAN", "SISE", "KCHOL", "BIMAS", "TUPRS", "ISCTR",
            "EKGYO", "KARDMD", "PETKM", "ARCLK", "HEKTS", "PGSUS", "KOZAL", "TCELL", "FROTO", "TOASO",
            "ENJSA", "GUBRF", "KONTR", "YEOTK", "SMRTG", "ALARK", "ODAS", "DOAS", "KCAER", "VAKBN",
            "HALKB", "ISMEN", "SAHOL", "YKBNK", "MGROS", "VESTL", "DOCO", "EGEEN", "TAVHL", "TKFEN",
            "ADESE", "AEFES", "AFYON", "AGESA", "AGHOL", "AKCNS", "AKENR", "AKFGY", "AKFYE", "ALBRK",
            "ALFAS", "ALGYO", "ALKA", "ALKIM", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARZUM",
            "ASGYO", "ASUZU", "ATAKP", "ATEKS", "AVPGY", "AYDEM", "AYGAZ", "BAGFS", "BANVT", "BERA",
            "BIENY", "BRLSM", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BVSAN", "CANTE", "CCOLA", "CEMTS",
            "CIMSA", "CWENE", "EBEBK", "ECILC", "ECZYT", "EGGUB", "ENKAI", "EUREN", "FENER", "GENIL",
            "GESAN", "GSDHO", "GWIND", "INVEO", "IPEKE", "ISDMR", "IZMDC", "KARSN", "KENT", "KERVT",
            "KLRGY", "KMPUR", "KONYA", "KORDS", "KOZAA", "LOGO", "MPARK", "NETAS", "OTKAR", "OYAKC",
            "QUAGR", "SKBNK", "SNGYO", "TTKOM", "TTRAK", "ULKER", "VESBE", "ZOREN"
        ]
        
        # Listeyi temizle ve Yahoo Finance formatına (.IS) çevir
        tum_liste = list(set(self.favoriler + self.ek_liste))
        self.hisseler = [h + ".IS" for h in sorted(tum_liste)]
        self.sonuclari = []

    def analiz_et(self, ticker):
        try:
            # Çoklu hisse taraması için timeout 15 saniyeye çıkarıldı
            df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True, progress=False, timeout=15)
            if df.empty or len(df) < 30: return None
            
            # Yahoo Multi-index sütun düzeltmesi
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df["RSI"] = ta.rsi(df["Close"], length=14)
            macd = ta.macd(df["Close"])
            df = pd.concat([df, macd], axis=1)
            df["SMA20"] = ta.sma(df["Close"], length=20)
            
            son = df.iloc[-1]
            puan = 0
            # 3'lü Onay Mekanizması
            if float(son["RSI"]) < 50: puan += 1
            if float(son["MACDh_12_26_9"]) > 0: puan += 1
            if float(son["Close"]) > float(son["SMA20"]): puan += 1

            sembol = ticker.replace(".IS", "")
            return {
                "Kod": sembol,
                "Fiyat": f"{float(son['Close']):.2f} TL",
                "RSI": f"{float(son['RSI']):.1f}",
                "Skor": f"{puan}/3",
                "Favori": sembol in self.favoriler
            }
        except Exception:
            return None

    def html_rapor_uret(self):
        zaman = datetime.now().strftime('%d/%m/%Y %H:%M')
        html = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <title>Hasan Bey 100+ Borsa Paneli</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; }}
                .container {{ max-width: 1000px; margin-top: 40px; }}
                .card {{ background: #1e293b; border-radius: 12px; border: none; }}
                .fav-row {{ background-color: #1e3a8a !important; color: #fff; font-weight: bold; border-left: 5px solid #3b82f6; }}
                .table {{ color: #e2e8f0; }}
            </style>
        </head>
        <body>
            <div class="container text-center">
                <div class="card p-4 shadow-lg">
                    <h2 class="mb-1">🎯 Stratejik Analiz Paneli (100+ Hisse)</h2>
                    <p class="text-secondary small mb-4">Son Güncelleme: {zaman}</p>
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead><tr><th>Hisse</th><th>Fiyat</th><th>RSI</th><th>Skor</th></tr></thead>
                            <tbody>
        """
        # Favoriler en üstte, sonra skor sırasına göre
        sirali = sorted(self.sonuclari, key=lambda x: (not x['Favori'], -int(x['Skor'][0])))
        for h in sirali:
            cls = "class='fav-row'" if h['Favori'] else ""
            html += f"<tr {cls}><td>{h['Kod']}</td><td>{h['Fiyat']}</td><td>{h['RSI']}</td><td>{h['Skor']}</td></tr>"
        
        html += "</tbody></table></div></div></div></body></html>"
        with open("index_yeni.html", "w", encoding="utf-8") as f:
            f.write(html)

    def telegram_bildir(self):
        # Sadece skoru 2 ve üzeri olan fırsatları gönder (Mesaj kalabalığını önler)
        firsatlar = [h for h in self.sonuclari if int(h['Skor'][0]) >= 2]
        if not firsatlar: return
        
        msg = f"🚀 *YENİ 100+ ANALİZ RAPORU*\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        for f in firsatlar[:15]: # Telegram limitine takılmamak için ilk 15
            emoji = "💎" if f['Favori'] else "✅"
            msg += f"{emoji} *{f['Kod']}*: {f['Fiyat']} (RSI: {f['RSI']})\n"
        
        try:
            requests.post(f"https://api.telegram.org/bot{self.TOKEN}/sendMessage", 
                          data={"chat_id": self.CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        except: pass

    def calistir(self):
        logging.info(f"Tarama başlatıldı: {len(self.hisseler)} hisse kontrol ediliyor...")
        for h in self.hisseler:
            res = self.analiz_et(h)
            if res: self.sonuclari.append(res)
            time.sleep(0.15) # API limitine takılmamak için kısa bekleme
            
        self.html_rapor_uret()
        self.telegram_bildir()
        logging.info("İşlem başarıyla tamamlandı.")

if __name__ == "__main__":
    YeniBorsaSistemi().calistir()
