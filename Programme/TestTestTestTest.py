from simple import MQTTClient
import network
import time

# WLAN-Verbindung
ssid = "KrustyKrab1"
password = "WerderBremen2501"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    pass
print("Verbunden mit:", wlan.ifconfig())

# MQTT-Setup
BROKER_IP = b"192.168.0.79"  # Ersetze durch deine PC-IP
BROKER_PORT = 1883  # Standardport
CLIENT_ID = b"ESP32_Client"
TOPIC = b"Zuhause/Wohnung/BloomBuddy"

try:
    client = MQTTClient(CLIENT_ID, BROKER_IP, port=BROKER_PORT)
    client.connect()
    print("Verbunden mit MQTT-Broker.")
    
    # Wartezeit, um sicherzustellen, dass die Verbindung hergestellt wurde
    time.sleep(1)
    
    client.publish(TOPIC, "Hallo von ESP32!")
    print("Nachricht gesendet!")
    
except OSError as e:
    print(f"Fehler bei der MQTT-Verbindung: {e}")
    
finally:
    try:
        client.disconnect()
        print("Verbindung getrennt.")
    except NameError:
        print("Keine Verbindung hergestellt.")

