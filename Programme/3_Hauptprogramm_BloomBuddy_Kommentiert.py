#-----------------------#
# Programm:    Automatische Pflanzenbewässerung
# Version:     V1.0
# Programmierer: Jerrit Schnaible
# Datum:       29.04.2025
#
# Beschreibung:
# Dieses Programm liest regelmäßig Sensordaten ein (Bodenfeuchtigkeit, Entfernung, Lufttemperatur,
# Luftfeuchtigkeit, Lichtintensität), wertet diese aus und steuert bei Bedarf eine Pumpe zur
# automatischen Bewässerung einer Pflanze. Die Sensordaten werden zusätzlich per MQTT veröffentlicht.
#
# Hardware:
# - ESP32 S3
# - Capacitive Soil Moisture Sensor V2.0.0 (analog)
# - AHT21 (Temperatur & Luftfeuchtigkeit)
# - BH1750 (Helligkeit)
# - VL53L0X (ToF Entfernung)
# - Relais zur Pumpensteuerung
# - AM325 Mini Pump
#-----------------------#

# === Bibliotheken einbinden ===
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

relais_in1 = Pin(7, Pin.OUT)
pumpe_laeuft = False
startzeit = 0

bodenfeuchte_sensor = Pin(15)
boden_adc = ADC(bodenfeuchte_sensor)
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

# === WLAN-Verbindung herstellen ===
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

# === MQTT-Verbindung aufbauen ===
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

# === Hauptprogrammschleife ===
while True:

    # --- Bodenfeuchtigkeit erfassen & Pumpensteuerung ---
    boden_adc_wert = boden_adc.read()
    bodenfeuchtigkeit = ((boden_adc_wert - nass_adc_wert) / (trocken_adc_wert - nass_adc_wert)) * (trocken_wert - nass_wert) + nass_wert
    bodenfeuchtigkeit = round(max(0, min(bodenfeuchtigkeit, 100)))
    print(f'Bodenfeuchtigkeit: {bodenfeuchtigkeit:.1f}%')

    if bodenfeuchtigkeit <= 40 and not pumpe_laeuft:
        relais_in1.value(1)
        startzeit = time.ticks_ms()
        pumpe_laeuft = True
        print("Relais angesteuert, Pumpe ein, Wasser läuft")

    if pumpe_laeuft:
        vergangene_zeit = time.ticks_diff(time.ticks_ms(), startzeit)
        if vergangene_zeit >= 15000:
            relais_in1.value(0)
            pumpe_laeuft = False
            print("Pumpe gestoppt nach 15 Sekunden")
    else:
        relais_in1.value(0)
        print("Relais nicht angesteuert, Pumpe aus")

    # --- Sensorwerte sammeln (ToF, AHT21, BH1750) ---
    fuellstand_roh = [tof_sensor.read() for _ in range(10)]
    temperatur_roh = []
    feuchtigkeit_roh = []
    helligkeit_roh = []

    for _ in range(10):
        aht21_sensor.measure()
        temperatur_roh.append(aht21_sensor.temperature)
        feuchtigkeit_roh.append(aht21_sensor.humidity)
        time.sleep(0.1)

    for _ in range(10):
        helligkeit_roh.append(bh1750_sensor.luminance(0x20))
        time.sleep(0.1)

    # --- Ausreißer entfernen & Mittelwerte berechnen ---
    def bereinigt_mittel(liste):
        if len(liste) > 2:
            liste.remove(max(liste))
            liste.remove(min(liste))
        return round(sum(liste) / len(liste))

    fuellstand = bereinigt_mittel(fuellstand_roh)
    temperatur = bereinigt_mittel(temperatur_roh)
    feuchtigkeit = bereinigt_mittel(feuchtigkeit_roh)
    helligkeit = bereinigt_mittel(helligkeit_roh)

    # --- Sensordaten als JSON aufbereiten & per MQTT senden ---
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

    # --- Energiesparlogik: Bei hoher Bodenfeuchtigkeit Pause einlegen ---
    if bodenfeuchtigkeit >= 80:
        print("ESP32 wird in Sleep versetzt")
        time.sleep(30)

    # --- Standardwartezeit zwischen Messzyklen ---
    time.sleep(15)
