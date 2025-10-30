import time
import requests
from PIL import Image, ImageDraw, ImageFont
import spidev
import RPi.GPIO as GPIO

# Pin-Definitionen
RST_PIN = 17
BUSY_PIN = 24
DC_PIN = 25
CS_PIN = 8
SCK_PIN = 11
MOSI_PIN = 10

# Initialisierung SPI etc. (abhängig von deiner Modul-Library)
spi = spidev.SpiDev(0, 0)
spi.max_speed_hz = 2000000

GPIO.setmode(GPIO.BCM)
GPIO.setup(RST_PIN, GPIO.OUT)
GPIO.setup(DC_PIN, GPIO.OUT)
GPIO.setup(CS_PIN, GPIO.OUT)
GPIO.setup(BUSY_PIN, GPIO.IN)

# Display-initialisierung hier: (Reset, Init, Clear etc.)
def epd_init():
    # Reset
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(RST_PIN, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(0.1)
    # … andere Init-Befehle je Modul …
    pass

def epd_display(image):
    # Bild (200×200) auf Display senden.
    # Modulabhängig: SPI senden, D/C setzen, CS setzen etc.
    pass

def get_gold_price(api_key):
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {"x-access-token": api_key}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    price = data["price"]          # USD pro Unze
    change = data["change"]        # Veränderung seit Vortag
    return price, change

def draw_image(price, change):
    img = Image.new('1', (200, 200), 255)  # 1-bit mode, weiß Hintergrund
    draw = ImageDraw.Draw(img)
    font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)

    draw.text((10, 30), f"Goldpreis:", font=font_large, fill=0)
    draw.text((10, 70), f"{price:.2f} USD/oz", font=font_large, fill=0)

    sign = "+" if change >= 0 else "-"
    draw.text((10, 120), f"{sign}{abs(change):.2f} USD seit gestern", font=font_small, fill=0)

    return img

def main_loop(api_key, interval_minutes=30):
    epd_init()
    while True:
        try:
            price, change = get_gold_price(api_key)
            img = draw_image(price, change)
            epd_display(img)
        except Exception as e:
            print("Fehler:", e)
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    API_KEY = "DEIN_API_KEY_HIER"
    main_loop(API_KEY)
