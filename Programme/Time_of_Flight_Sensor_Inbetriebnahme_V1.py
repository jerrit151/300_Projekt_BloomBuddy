'''
#-----------------------#
Programm: 		Inbetriebnahme TOF-Sensor
Version: 		V1.0

Programmierer: 	Schnaible
Datum:			12.03.2025

Hardware:       ESP32 S3
Sensor: 		VL53L0X
#-----------------------#
'''

import machine
import time
from machine import I2C
import VL53L0X

# I2C Konfiguration
i2c = I2C(0, scl=machine.Pin(14), sda=machine.Pin(13))

# VL53L0X Objekt erstellen
tof_sensor = VL53L0X.VL53L0X(i2c)

# Messung alle 10 Sekunden
while True:
    # Entfernung messen
    distance = tof_sensor.read()
    
    # Wert ausgeben
    print(f"Entfernung: {distance} mm")
    
    # Warten bis zur nächsten Messung
    time.sleep(10)
