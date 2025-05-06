# 300_Projekt_BloomBuddy
README – BloomBuddy: Smarte Pflanzenbewässerung
BloomBuddy ist ein automatisiertes Bewässerungssystem für Zimmerpflanzen, das mithilfe von Sensoren die wichtigsten Umgebungsparameter überwacht und die Bewässerung selbstständig steuert. Das System misst Bodenfeuchtigkeit, Temperatur, Luftfeuchtigkeit, Helligkeit und den Füllstand des Wassertanks. Die Steuerung und Visualisierung erfolgt über Node-RED, alle Messdaten werden in einer Datenbank gespeichert. Bei niedrigem Tankfüllstand wird automatisch eine Push-Benachrichtigung per E-Mail versendet.

Funktionen
Automatische Bewässerung je nach gemessener Bodenfeuchtigkeit

Messung und Überwachung von:

Bodenfeuchtigkeit (kapazitiver Sensor)

Temperatur und Luftfeuchtigkeit (AHT21)

Helligkeit (BH1750)

Tankfüllstand (VL53L0X ToF-Sensor)

Manuelle Steuerung der Pumpe über das Node-RED Dashboard

Push-Benachrichtigung bei niedrigem Tankfüllstand (< 20 %)

Speicherung aller Sensordaten in einer MariaDB/HeidiSQL-Datenbank

Visualisierung aller Werte und Steuerung über Node-RED

Benötigte Komponenten
ESP32 S3 Mikrocontroller

Kapazitiver Bodenfeuchtesensor

AHT21 (Temp./Feuchte)

BH1750 (Helligkeit)

VL53L0X (Füllstand)

5V Relais, AM325 Mini-Pumpe, 5V Netzteil

Node-RED, Thonny IDE, Mosquitto MQTT-Broker, MariaDB, HeidiSQL

Inbetriebnahme
Sensoren und Aktoren gemäß Anleitung anschließen.

MicroPython-Code mit Thonny auf den ESP32 übertragen.

Node-RED, MQTT-Broker und Datenbank einrichten.

WLAN-Zugangsdaten und MQTT-Parameter im Code anpassen.

System einschalten und über das Node-RED Dashboard bedienen.

Bedienung
Das System arbeitet standardmäßig im Automatikmodus.

Die Pumpe kann jederzeit manuell über das Dashboard ein- und ausgeschaltet werden (Handbetrieb hat Vorrang).

Alle Sensordaten und Systemzustände sind im Dashboard einsehbar.

Bei niedrigem Wasserstand erfolgt eine automatische Benachrichtigung.

Weitere Hinweise
Sensoren sollten regelmäßig auf Verschmutzung geprüft und ggf. kalibriert werden.

Der Wassertank muss rechtzeitig nachgefüllt werden, damit die automatische Bewässerung funktioniert.

Das System ist modular erweiterbar und kann auf weitere Pflanzen angepasst werden.

Weitere Details, Schaltpläne und den vollständigen Code finden Sie im GitHub-Repository.
