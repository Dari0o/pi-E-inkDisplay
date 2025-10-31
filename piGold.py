#!/usr/bin/env python3
import requests
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# E-Paper-Modul importieren
from seeed_python_epd import epd1in54  # SEENGREAT nutzt meist waveshare-kompatibles Modul

def get_gold_7day_change():
    """Holt Goldpreis der letzten 7 Tage von Yahoo Finance"""
    url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?region=US&lang=en-US&interval=1d&range=7d"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    }

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

    return price_now, change_abs, change_pct


def show_on_epaper(lines):
    """Zeigt Textzeilen auf dem 1.54-Zoll-E-Paper-Display an"""
    epd = epd1in54.EPD()
    epd.init()
    epd.Clear(0xFF)

    image = Image.new("1", (epd.width, epd.height), 255)  # weißer Hintergrund
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    y = 0
    for line in lines:
        draw.text((0, y), line, font=font, fill=0)
        y += 15  # Zeilenabstand

    epd.display(epd.getbuffer(image))
    epd.sleep()


def main():
    print("Starte Goldpreis-Monitor (Ctrl + C zum Beenden)")

    try:
        while True:
            try:
                price, change_abs, change_pct = get_gold_7day_change()

                # Ausgabe-Text (Konsole + E-Paper)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                output_lines = [
                    "📊 Goldpreis (7 Tage)",
                    f"Zeit: {now}",
                    f"Aktuell: {price:.2f} USD/oz",
                    f"Änderung: {change_abs:+.2f} USD",
                    f"Prozent: {change_pct:+.2f} %"
                ]

                # Konsolenausgabe
                print("\n" + "\n".join(output_lines))

                # E-Paper aktualisieren
                show_on_epaper(output_lines)

            except Exception as e:
                print("Fehler beim Abrufen:", e)

            # Alle 5 Minuten aktualisieren
            time.sleep(300)

    except KeyboardInterrupt:
        print("\n👋 Programm beendet. Gute Trades, Brudi!")


if __name__ == "__main__":
    main()
