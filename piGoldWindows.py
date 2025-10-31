import requests
import time
from datetime import datetime

def get_gold_7day_change():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?region=US&lang=en-US&interval=1d&range=7d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        chart = data["chart"]["result"][0]
        closes = chart["indicators"]["quote"][0]["close"]

        if len(closes) < 2:
            raise Exception("Zu wenige Daten erhalten")

        price_now = closes[-1]
        price_7days_ago = closes[0]

        change_abs = price_now - price_7days_ago
        change_pct = (change_abs / price_7days_ago) * 100

        print("\nGoldpreis (7 Tage Verlauf)")
        print(f"Zeit:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Vor 7 Tagen: {price_7days_ago:.2f} USD/oz")
        print(f"Jetzt:       {price_now:.2f} USD/oz")
        print(f"Änderung:    {change_abs:+.2f} USD  ({change_pct:+.2f}%)")

    except Exception as e:
        print("Fehler beim Abrufen:", e)


if __name__ == "__main__":
    print("Starte Goldpreis-Monitor... (Beenden mit Ctrl + C)")
    try:
        while True:
            get_gold_7day_change()
            time.sleep(300)  # 300 Sekunden = 5 Minuten warten
    except KeyboardInterrupt:
        print("\nProgramm beendet. Gute Trades, Brudi!")
