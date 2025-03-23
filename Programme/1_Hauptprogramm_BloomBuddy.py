import machine
import time
import network
from simple import MQTTClient
from machine import SoftI2C
import VL53L0X
from bh1750 import BH1750
from aht import AHT21
import json

# I2C-Bus konfigurieren (gemeinsam für beide Sensoren)
i2c = SoftI2C(scl=machine.Pin(12), sda=machine.Pin(13))

# Sensoren initialisieren
aht21_sensor = AHT21(i2c)
tof_sensor = VL53L0X.VL53L0X(i2c)
bh1750_sensor = BH1750(i2c)

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
    # Listen zum speichern der Messwerte
    fuellstand_roh = []
    temperatur_roh = []
    feuchtigkeit_roh = []
    helligkeit_roh = []

    for i in range(10):
        fuellstand_roh.append(tof_sensor.read())
        time.sleep(0.1)

    for i in range(10):
        # Messung muss getriggert werden damit die Liste gefüllt werden kann
        aht21_sensor.measure()
        temperatur_roh.append(aht21_sensor.temperature)
        feuchtigkeit_roh.append(aht21_sensor.humidity)
        time.sleep(0.1)
        
    for i in range(10):
        # ONCE_HIRES_1-Modus, wird verwendet da dieser in der Bibliothek verwendet wird
        helligkeit_roh.append(bh1750_sensor.luminance(0x20))
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
        
    if len(helligkeit_roh) > 2:     
        helligkeit_roh.remove(max(helligkeit_roh))
        helligkeit_roh.remove(min(helligkeit_roh))

    # Durchschnittswerte berechnen für eine höhere Genauigkeit
    fuellstand = round(sum(fuellstand_roh) / len(fuellstand_roh))
    temperatur = round(sum(temperatur_roh) / len(temperatur_roh))
    feuchtigkeit = round(sum(feuchtigkeit_roh) / len(feuchtigkeit_roh))
    helligkeit = round(sum(helligkeit_roh) / len(helligkeit_roh))
    
    # Ergebnisse ausgeben
    print(f"Entfernung: {fuellstand} mm")
    print(f"Durchschnittliche Temperatur: {temperatur}°C")
    print(f"Durchschnittliche Luftfeuchtigkeit: {feuchtigkeit}%")
    print(f"Durchschnittliche Helligkeit: {helligkeit}lux")

    # Daten als JSON-Objekt erstellen
    data = {
        "Fuellstand": fuellstand,
        "Temperatur": temperatur,
        "Luftfeuchtigkeit": feuchtigkeit,
        "Helligkeit": helligkeit
    }
    
    # JSON-Objekt in eine Zeichenkette umwandeln
    json_data = json.dumps(data)
    
    # JSON-Daten über MQTT senden
    client.publish(TOPIC, json_data)
    
    # Listen nach Berechnung leeren um falsche Messwerte zu vermeiden
    fuellstand_roh.clear()
    temperatur_roh.clear()
    feuchtigkeit_roh.clear()
    helligkeit_roh.clear()
    # Prüfen, ob die Liste wirklich leer ist
    print("Liste nach dem Leeren:", fuellstand_roh)
    print("Liste nach dem Leeren:", temperatur_roh)
    print("Liste nach dem Leeren:", feuchtigkeit_roh)
    print("Liste nach dem Leeren:", helligkeit_roh)
    # Rückmeldung ob der Wert gesendet wurde
    print(f"Sensordaten gesendet: {json_data}")
    
    time.sleep(20)
