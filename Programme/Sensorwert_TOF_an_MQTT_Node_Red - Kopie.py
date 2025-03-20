import machine
import time
import network
from simple import MQTTClient
from machine import I2C
import VL53L0X
import aht21
import json

# I2C Konfiguration VL53L0X/1XV2
i2c = I2C(0, scl=machine.Pin(12), sda=machine.Pin(13))
# I2C Konfiguration AHT21
i2c = I2C(1, scl=machine.Pin(4), sda=machine.Pin(5))

# VL53L0X Objekt erstellen
tof_sensor = VL53L0X.VL53L0X(i2c)
# AHT21-Sensor initialisieren
aht21_sensor = ahtx0.AHT21(i2c)

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

    # Listen zum Speichern der Messwerte
    fuellstand_roh = []
    temperaturwerte_roh = []
    feuchtigkeitswerte_roh = []

    # 10 Messwerte aufnehmen für den Fuellstand des Wassertanks
    for i in range(10):
        fuellstand_roh.append(tof_sensor.read())
        time.sleep(0.1)  # Kurze Pause zwischen den Messungen
        
    # 10 Messwerte aufnehmen für die Temperatur und die Luftfeuchtigkeit
    for i in range(10):
        temperatur_roh.append(sensor.measurements[0])  # Temperatur auslesen
        feuchtigkeit_roh.append(sensor.measurements[1])  # Luftfeuchtigkeit auslesen
        time.sleep(0.1)  # Kurze Pause zwischen den Messungen

    # Höchsten und niedrigsten Wert entfernen TOF-Sensor
    fuellstand_roh.remove(max(fuellstand_roh))  # Entfernt den höchsten Wert
    fuellstand_roh.remove(min(fuellstand_roh))  # Entfernt den niedrigsten Wert
    
    # Höchsten und niedrigsten Wert entfernen AHT21-Sensor
    temperatur_roh.remove(max(temperatur_roh))
    temperatur_roh.remove(min(temperatur_roh))
    feuchtigkeit_roh.remove(max(feuchtigkeit_roh))
    feuchtigkeit_roh.remove(min(feuchtigkeit_roh))

    # Messwerte in der Liste kontrollieren
    print("Fuellstand des Tanks:",fuellstand_roh)
    print("Temperatur-Rohwerte:", temperatur_roh)
    print("Feuchtigkeits-Rohwerte:", feuchtigkeit_roh)

    # Mittelwert berechnen
    fuellstand = round(sum(fuellstand_roh) / len(fuellstand_roh))
    temperatur = round(sum(temperatur_roh) / len(temperatur_roh), 2)
    feuchtigkeit = round(sum(feuchtigkeit_roh) / len(feuchtigkeit_roh), 2)
    
    # Ergebnisse ausgeben
    print(f"Entfernung: {fuellstand} mm")
    print(f"Durchschnittliche Temperatur: {temperatur}°C")
    print(f"Durchschnittliche Luftfeuchtigkeit: {feuchtigkeit}%")
    
    # Daten als JSON-Objekt erstellen
    data = {
        "Fuellstand": fuellstand,
        "Temperatur": temperatur,
        "Luftfeuchtigkeit": feuchtigkeit
    }
    
    # JSON-Objekt in eine Zeichenkette umwandeln
    json_data = json.dumps(data)
    
    # JSON-Daten über MQTT senden
    client.publish(TOPIC, json_data)
    
    # Listen nach Berechnung leeren um falsche Messwerte zu vermeiden
    fuellstand_roh.clear()
    temperatur_roh.clear()
    feuchtigkeit_roh.clear()
    # Prüfen, ob die Liste wirklich leer ist
    print("Liste nach dem Leeren:", fuellstand_roh)
    print("Liste nach dem Leeren:", temperatur_roh)
    print("Liste nach dem Leeren:", feuchtigkeit_roh)
    # Rückmeldung ob der Wert gesendet wurde
    print(f"Sensordaten gesendet: {json_data}")
    
    time.sleep(20)

