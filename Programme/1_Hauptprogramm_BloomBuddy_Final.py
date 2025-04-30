#-----------------------#
# Projekt: 		BloomBuddy
# Programm:    	Automatische Pflanzenbewässerung
# Version:     	V1.0
# Programmierer: Jerrit Schnaible
# Datum:       	29.04.2025
#
# Beschreibung:
# Dieses Programm liest regelmäßig Sensordaten ein (Bodenfeuchtigkeit, Entfernung (Füllstand), Temperatur,
# Luftfeuchtigkeit und Helligkeit), wertet diese aus und steuert bei Bedarf eine Pumpe zur
# automatischen Bewässerung einer Pflanze an. Die Sensordaten werden zusätzlich per MQTT veröffentlicht,
# mit Node-Red verarbeitet und anschließend auf der UI angezeigt. Unter anderem werden die Daten per Node-Red
# auch in eine Datenbank (MariaDB) geschrieben und eine Push-Benachrichtigung ausgegeben wenn der Füllstand des Wassertanks unter
# 20% fällt. In diesem Fall wird dann eine E-Mail versandt. Zusätzlich kann die Pumpe manuell über das Node-Red-Dashboard gesteuert werden.
# Die manuelle Steuerung der Pumpe hat jederzeit Vorrang vor dem Automatikbetrieb
#
# Hardware:
# - ESP32 S3
# - Capacitive Soil Moisture Sensor V2.0.0 (analog)
# - AHT21 (Temperatur & Luftfeuchtigkeit)
# - BH1750 (Helligkeit)
# - VL53L0X (ToF Entfernungssensor)
# - 5V Relais zur Pumpensteuerung
# - AM325 Mini Pumpe
#-----------------------#

# === Bibliotheken einbinden ===

# Hardwarezugriff: GPIO, ADC, PWM, I2C, SPI usw.
import machine
from machine import Pin, ADC, SoftI2C
# Zeitfunktionen (z. B. sleep, ticks_ms)
import time
# WLAN- und Netzwerkfunktionen
import network
# MQTT Kommunikation
from umqtt.simple import MQTTClient
# TOF Entfernungssensor
import VL53L0X
# Helligkeitssensor
from bh1750 import BH1750
# Temperatur und Luftfeuchtigkeitssensor
from aht import AHT21
# JSON Dateiformat
import json

# === Initialisierung der Sensorik & Hardware-Komponenten ===

# I2C-Bus konfigurieren (gemeinsam für alle drei I2C-fähigen-Sensoren, ein I2C-Bus wird verwendet)
i2c = SoftI2C(scl=machine.Pin(4), sda=machine.Pin(5))

# Ausgangs-Pin für das Relais definieren, Werte initialiseren
relais = Pin(8, Pin.OUT)
pumpe_laeuft = False
startzeit = 0
#Variablen für die Steuerung der Pumpe per MQTT über Node-Red
manueller_modus = False
automatik_modus = True

# ADC-Pin für den Sensor
bodenfeuchte_sensor = Pin(15)
boden_adc = ADC(bodenfeuchte_sensor)

# ADC-Einstellungen
boden_adc.atten(ADC.ATTN_11DB)  # Vollbereich: 3.3V
boden_adc.width(ADC.WIDTH_12BIT)  # Bereich: 0 bis 4095

# === Kalibrierung des Capacitive Soil Moisture Sensors ===

trocken_wert = 0  # Trockener Boden
nass_wert = 100  # Nasser Boden

# ADC-Werte für einen trockenen und einen nassen Boden
# (müssen experimentell ermittelt werden, je nachdem wie Nass der Boden für die Pflanze sein soll)
# Hier sind Platzhalter, werden je nach Pflanze auf tatsächlichen ADC-Werte gesetzt
trocken_adc_wert = 3070  # Beispielwert für trockenen Boden, reagiert sehr empfindlich auf kleine Änderungen mit diesem Wert in der Luft ca. 2%
nass_adc_wert = 1700  # Beispielwert für nassen Boden

# === Sensorinstanzen ===

# Sensoren initialisieren
aht21_sensor = AHT21(i2c)
tof_sensor = VL53L0X.VL53L0X(i2c)
bh1750_sensor = BH1750(i2c)

# === WLAN-Verbindung herstellen ===

# WLAN-Parameter für die Schule
#ssid = 'BZTG-IoT'
#password = 'WerderBremen24'

# WLAN-Parameter für Zuhause
ssid = 'KrustyKrab2'
password = 'WerderBremen2501'

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

# === MQTT-Verbindung aufbauen ===

# MQTT-Setup
BROKER_IP = b"192.168.33.79"
BROKER_PORT = 1883
CLIENT_ID = b"ESP32_Client"
TOPIC = b"Zuhause/Wohnung/BloomBuddy"

# MQTT-Client erstellen und verbinden
client = MQTTClient(CLIENT_ID, BROKER_IP, port=BROKER_PORT)

try:
    client.connect()
except Exception as e:
    print(f"Fehler beim Verbinden: {e}")
    while True:
        pass

# MQTT Nachrichten Abfrage zur Steuerung der Pumpe über den Handbetrieb
# --- MQTT Callback ---
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
    
    client.check_msg()  # Prüft, ob neue MQTT-Nachricht da ist

    # --- Bodenfeuchtigkeit erfassen & Pumpensteuerung ---
    
    # Sensorwert lesen
    boden_adc_wert = boden_adc.read()
        
    # Berechnung des Feuchtigkeitswertes basierend auf den Kalibrierwerten
    bodenfeuchtigkeit = ((boden_adc_wert - nass_adc_wert) / (trocken_adc_wert - nass_adc_wert)) * (trocken_wert - nass_wert) + nass_wert
        
    # Sicherstellen, dass der Wert im Bereich von 0 bis 100 bleibt und gerundet wird
    bodenfeuchtigkeit = round(max(0, min(bodenfeuchtigkeit, 100)))
    print(f'Bodenfeuchtigkeit: {bodenfeuchtigkeit:.1f}%')

    # --- Pumpensteuerung ---
    
    # --- Automatikbetrieb ---
    if automatik_modus and bodenfeuchtigkeit <= 40 and not pumpe_laeuft:
        relais.value(1)  # Relais EIN (HIGH)
        startzeit = time.ticks_ms()
        pumpe_laeuft = True
        print("Automatik: Relais EIN (wegen geringer Bodenfeuchtigkeit)")

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
    
    # Listen zum speichern der Messwerte
    fuellstand_roh = []
    temperatur_roh = []
    feuchtigkeit_roh = []
    helligkeit_roh = []

    for i in range(10):
        client.check_msg()  # Neue Nachrichten über MQTT prüfen
        # Messung muss getriggert werden damit die Liste gefüllt werden kann
        fuellstand_roh.append(tof_sensor.read())
        time.sleep(0.1)

    for i in range(10):
        client.check_msg()  # Neue Nachrichten über MQTT prüfen
        # Messung muss getriggert werden damit die Liste gefüllt werden kann, Messwerte werden in die Liste geschrieben
        aht21_sensor.measure()
        temperatur_roh.append(aht21_sensor.temperature)
        feuchtigkeit_roh.append(aht21_sensor.humidity)
        time.sleep(0.1)
        
    for i in range(10):
        client.check_msg()  # Neue Nachrichten über MQTT prüfen
        # ONCE_HIRES_1-Modus, wird verwendet da dieser in der Bibliothek verwendet wird, dieser löst Messung aus
        helligkeit_roh.append(bh1750_sensor.luminance(0x20))
        time.sleep(0.1)
    
    # --- Ausreißer entfernen & Mittelwerte berechnen ---
    
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

    # Mittelwerte berechnen für eine höhere Genauigkeit
    fuellstand = round(sum(fuellstand_roh) / len(fuellstand_roh))
    temperatur = round(sum(temperatur_roh) / len(temperatur_roh))
    feuchtigkeit = round(sum(feuchtigkeit_roh) / len(feuchtigkeit_roh))
    helligkeit = round(sum(helligkeit_roh) / len(helligkeit_roh))
    
    # Ergebnisse ausgeben
    print(f"Entfernung: {fuellstand} mm")
    print(f"Durchschnittliche Temperatur: {temperatur}°C")
    print(f"Durchschnittliche Luftfeuchtigkeit: {feuchtigkeit}%")
    print(f"Durchschnittliche Helligkeit: {helligkeit}lux")
    
    # --- Sensordaten als JSON aufbereiten & per MQTT senden ---
    
    # Daten als JSON-Objekt erstellen
    data = {
        "Fuellstand": fuellstand,
        "Temperatur": temperatur,
        "Luftfeuchtigkeit": feuchtigkeit,
        "Helligkeit": helligkeit,
        "Bodenfeuchtigkeit": bodenfeuchtigkeit
    }
    
    # JSON-Objekt in eine Zeichenkette umwandeln
    json_data = json.dumps(data)
    
    # JSON-Daten über MQTT senden
    client.publish(TOPIC, json_data)
    
    # Rückmeldung ob der Wert gesendet wurde
    print(f"Sensordaten gesendet: {json_data}")
    
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
        
    # --- Standardwartezeit zwischen Messzyklen ---
    
    time.sleep(5)
       