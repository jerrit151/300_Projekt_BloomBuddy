# Projekt:         BloomBuddy
# Programm:        Automatische Pflanzenbewässerung mit manuellem Vorrang
# Version:         V1.1
# Programmierer:   Jerrit Schnaible
# Datum:           30.04.2025

import machine
from machine import Pin, ADC, SoftI2C
import time
import network
from umqtt.simple import MQTTClient
import VL53L0X
from bh1750 import BH1750
from aht import AHT21
import json

# === Initialisierung der Sensorik & Hardware-Komponenten ===

i2c = SoftI2C(scl=machine.Pin(4), sda=machine.Pin(5))

# Relais an Pin 18, HIGH = EIN, LOW = AUS
relais = Pin(8, Pin.OUT)
pumpe_laeuft = False
startzeit = 0
manueller_modus = False
automatik_modus = True

# ADC-Pin für Bodenfeuchtesensor
boden_adc = ADC(Pin(15))
boden_adc.atten(ADC.ATTN_11DB)
boden_adc.width(ADC.WIDTH_12BIT)

# Kalibrierung
trocken_wert = 0
nass_wert = 100
trocken_adc_wert = 3070
nass_adc_wert = 1700

# Sensorinstanzen
aht21_sensor = AHT21(i2c)
tof_sensor = VL53L0X.VL53L0X(i2c)
bh1750_sensor = BH1750(i2c)

# WLAN-Parameter
ssid = 'KrustyKrab2'
password = 'WerderBremen2501'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

timeout = 10
while not wlan.isconnected() and timeout > 0:
    time.sleep(1)
    timeout -= 1

if not wlan.isconnected():
    print("WLAN-Verbindung fehlgeschlagen!")
    while True:
        pass

print('WLAN verbunden')

# MQTT-Setup
BROKER_IP = b"192.168.33.79"
BROKER_PORT = 1883
CLIENT_ID = b"ESP32_Client"
TOPIC = b"Zuhause/Wohnung/BloomBuddy"

client = MQTTClient(CLIENT_ID, BROKER_IP, port=BROKER_PORT)

try:
    client.connect()
except Exception as e:
    print(f"Fehler beim Verbinden: {e}")
    while True:
        pass

# --- MQTT Callback Funktion ---
def sub_relais(topic, msg):
    global manueller_modus, pumpe_laeuft, startzeit, automatik_modus
    daten = json.loads(msg)
    schalter1 = daten.get('Schalter1')
    if schalter1 == "ON":
        relais.value(1)  # Relais EIN (HIGH)
        manueller_modus = True
        automatik_modus = False
        pumpe_laeuft = True
        startzeit = time.ticks_ms()
        print("Relais EIN (manuell)")
    elif schalter1 == "OFF":
        relais.value(0)  # Relais AUS (LOW)
        manueller_modus = False
        automatik_modus = True
        pumpe_laeuft = False
        print("Relais AUS (manuell)")

client.set_callback(sub_relais)
client.subscribe(TOPIC)
print("MQTT-Abonnement auf", TOPIC.decode(), "aktiviert")

# === Hauptprogrammschleife ===

while True:
    client.check_msg()

    # --- Bodenfeuchtigkeit erfassen & Pumpensteuerung ---
    boden_adc_wert = boden_adc.read()
    bodenfeuchtigkeit = ((boden_adc_wert - nass_adc_wert) / (trocken_adc_wert - nass_adc_wert)) * (trocken_wert - nass_wert) + nass_wert
    bodenfeuchtigkeit = round(max(0, min(bodenfeuchtigkeit, 100)))
    print(f'Bodenfeuchtigkeit: {bodenfeuchtigkeit:.1f}%')

    # --- Automatikbetrieb ---
    if automatik_modus and bodenfeuchtigkeit <= 40 and not pumpe_laeuft:
        relais.value(1)  # Relais EIN (HIGH)
        startzeit = time.ticks_ms()
        pumpe_laeuft = True
        print("Automatik: Relais EIN (wegen Bodenfeuchtigkeit)")

    if pumpe_laeuft:
        vergangene_zeit = time.ticks_diff(time.ticks_ms(), startzeit)
        if manueller_modus:
            print(f"Relais läuft manuell seit {vergangene_zeit} ms")
            # Keine Zeitabschaltung im manuellen Modus
        else:
            if vergangene_zeit >= 15000:
                relais.value(0)  # Relais AUS (LOW)
                pumpe_laeuft = False
                print("Automatik: Relais AUS nach 15 Sekunden")

    if not pumpe_laeuft and not manueller_modus:
        relais.value(0)
        print("Relais bleibt AUS")

    # --- Sensorwerte sammeln (ToF, AHT21, BH1750) ---
    fuellstand_roh = []
    temperatur_roh = []
    feuchtigkeit_roh = []
    helligkeit_roh = []

    for i in range(10):
        client.check_msg()
        fuellstand_roh.append(tof_sensor.read())
        time.sleep(0.1)

    for i in range(10):
        client.check_msg()
        aht21_sensor.measure()
        temperatur_roh.append(aht21_sensor.temperature)
        feuchtigkeit_roh.append(aht21_sensor.humidity)
        time.sleep(0.1)

    for i in range(10):
        client.check_msg()
        helligkeit_roh.append(bh1750_sensor.luminance(0x20))
        time.sleep(0.1)

    if len(fuellstand_roh) > 2:
        fuellstand_roh.remove(max(fuellstand_roh))
        fuellstand_roh.remove(min(fuellstand_roh))
    if len(temperatur_roh) > 2:
        temperatur_roh.remove(max(temperatur_roh))
        temperatur_roh.remove(min(temperatur_roh))
    if len(feuchtigkeit_roh) > 2:
        feuchtigkeit_roh.remove(max(feuchtigkeit_roh))
        feuchtigkeit_roh.remove(min(feuchtigkeit_roh))
    if len(helligkeit_roh) > 2:
        helligkeit_roh.remove(max(helligkeit_roh))
        helligkeit_roh.remove(min(helligkeit_roh))

    fuellstand = round(sum(fuellstand_roh) / len(fuellstand_roh))
    temperatur = round(sum(temperatur_roh) / len(temperatur_roh))
    feuchtigkeit = round(sum(feuchtigkeit_roh) / len(feuchtigkeit_roh))
    helligkeit = round(sum(helligkeit_roh) / len(helligkeit_roh))

    print(f"Entfernung: {fuellstand} mm")
    print(f"Durchschnittliche Temperatur: {temperatur}°C")
    print(f"Durchschnittliche Luftfeuchtigkeit: {feuchtigkeit}%")
    print(f"Durchschnittliche Helligkeit: {helligkeit}lux")

    data = {
        "Fuellstand": fuellstand,
        "Temperatur": temperatur,
        "Luftfeuchtigkeit": feuchtigkeit,
        "Helligkeit": helligkeit,
        "Bodenfeuchtigkeit": bodenfeuchtigkeit
    }

    json_data = json.dumps(data)
    client.publish(TOPIC, json_data)
    print(f"Sensordaten gesendet: {json_data}")

    fuellstand_roh.clear()
    temperatur_roh.clear()
    feuchtigkeit_roh.clear()
    helligkeit_roh.clear()
