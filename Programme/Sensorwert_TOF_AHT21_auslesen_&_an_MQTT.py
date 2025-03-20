import machine
import time
import network
from simple import MQTTClient
from machine import SoftI2C
import VL53L0X
from aht import AHT21
import json

# I2C-Bus konfigurieren (gemeinsam für beide Sensoren)
i2c = SoftI2C(scl=machine.Pin(12), sda=machine.Pin(13))

# Sensoren initialisieren
aht21_sensor = AHT21(i2c)
tof_sensor = VL53L0X.VL53L0X(i2c)

# WLAN-Parameter
ssid = 'KrustyKrab2'
password = 'WerderBremen2501'

# MQTT-Setup
BROKER_IP = b"192.168.33.79"
BROKER_PORT = 1883
CLIENT_ID = b"ESP32_Client"
TOPIC = b"Zuhause/Wohnung/BloomBuddy"

# WLAN verbinden
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

# MQTT-Client erstellen und verbinden
client = MQTTClient(CLIENT_ID, BROKER_IP, port=BROKER_PORT)
try:
    client.connect()
except Exception as e:
    print(f"Fehler beim Verbinden: {e}")
    while True:
        pass

while True:
    # Messwerte sammeln
    fuellstand_roh = []
    temperatur_roh = []
    feuchtigkeit_roh = []

    for i in range(10):
        fuellstand_roh.append(tof_sensor.read())
        time.sleep(0.1)

    for i in range(10):
        # Messung muss getriggert werden damit die Liste gefüllt werden kann
        aht21_sensor.measure()
        temperatur_roh.append(aht21_sensor.temperature)
        feuchtigkeit_roh.append(aht21_sensor.humidity)
        time.sleep(0.1)

    # Höchsten und Niedrigsten Messwert entfernen aus den jeweiligen Listen entfernen
    if len(fuellstand_roh) > 2:
        fuellstand_roh.remove(max(fuellstand_roh))
        fuellstand_roh.remove(min(fuellstand_roh))

    if len(temperatur_roh) > 2:
        temperatur_roh.remove(max(temperatur_roh))
        temperatur_roh.remove(min(temperatur_roh))
    
    if len(feuchtigkeit_roh) > 2:
        feuchtigkeit_roh.remove(max(feuchtigkeit_roh))
        feuchtigkeit_roh.remove(min(feuchtigkeit_roh))

    # Durchschnittswerte berechnen für eine höhere Genauigkeit
    fuellstand = round(sum(fuellstand_roh) / len(fuellstand_roh))
    temperatur = round(sum(temperatur_roh) / len(temperatur_roh))
    feuchtigkeit = round(sum(feuchtigkeit_roh) / len(feuchtigkeit_roh))

    # Daten als JSON senden
    data = {
        "Fuellstand": fuellstand,
        "Temperatur": temperatur,
        "Luftfeuchtigkeit": feuchtigkeit
    }
    json_data = json.dumps(data).encode()

    client.publish(TOPIC, json_data)
    print(f"Sensordaten gesendet: {json_data}")
    # Messung wird alle 20sek wiederholt, im späteren Betrieb soll die Zeit deutlich länger sein
    time.sleep(20)
