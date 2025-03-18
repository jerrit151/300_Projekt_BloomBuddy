import machine
import time
import network
from simple import MQTTClient
from machine import I2C
import VL53L0X
import json

# I2C Konfiguration
i2c = I2C(0, scl=machine.Pin(14), sda=machine.Pin(13))

# VL53L0X Objekt erstellen
tof_sensor = VL53L0X.VL53L0X(i2c)

# WLAN-Parameter
ssid = 'KrustyKrab2'
password = 'WerderBremen2501'

# MQTT-Setup
BROKER_IP = b"192.168.33.79"  # Ersetze durch deine PC-IP
BROKER_PORT = 1883  # Standardport
CLIENT_ID = b"ESP32_Client"
TOPIC = b"Zuhause/Wohnung/BloomBuddy"

# WLAN-Verbindung herstellen
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    pass

print('WLAN verbunden')

# MQTT-Client erstellen
client = MQTTClient(CLIENT_ID, BROKER_IP, port=BROKER_PORT)

# Verbindung zum MQTT-Broker herstellen
try:
    client.connect()
except Exception as e:
    print(f"Fehler beim Verbinden: {e}")
    while True:
        pass

while True:

# Liste zum Speichern der Messwerte
    fuellstand_roh = []
    
# 10 Messwerte aufnehmen
    for i in range(10):
        fuellstand_roh.append(tof_sensor.read())
        time.sleep(0.1)  # Kurze Pause zwischen den Messungen

    # Ersten und letzten Wert mit pop() entfernen
    fuellstand_roh.pop(0)  # Entfernt den ersten Wert
    fuellstand_roh.pop()   # Entfernt den letzten Wert
    
    #Messwerte in der Liste kontrollieren
    print(fuellstand_roh)
    
    # Mittelwert berechnen
    fuellstand = round(sum(fuellstand_roh) / len(fuellstand_roh))
    
    print(f"Entfernung: {fuellstand} mm")
    
    # Daten als JSON-Objekt erstellen
    data = {
        "Fuellstand": fuellstand
    }
    
    # JSON-Objekt in eine Zeichenkette umwandeln
    json_data = json.dumps(data)
    
    # JSON-Daten über MQTT senden
    client.publish(TOPIC, json_data)
    
    # Liste nach Berechnung leeren um falsche Messwerte zu vermeiden
    fuellstand_roh.clear()
    # Prüfen, ob die Liste wirklich leer ist
    print("Liste nach dem Leeren:", fuellstand_roh)
    # Rückmeldung ob der Wert gesendet wurde
    print(f"Sensordaten gesendet: {json_data}")
    
    time.sleep(30)

