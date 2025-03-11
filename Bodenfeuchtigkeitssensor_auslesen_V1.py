'''
#-----------------------#
Programm: 		Bodenfeuchtigkeit messen
Version: 		V1.0

Programmierer: 	Schnaible
Datum:			11.03.2025

Hardware:       ESP32 S3
Sensor: 		Capacitive Soil Moisture Sensor V2.0.0
#-----------------------#
'''

from machine import ADC, Pin
import time

#Mit diesem PIN ist der Bodenfeuchtigkeitssensor verbunden
AOUT_PIN = 1_4

#Analog-Pin auf Lesen einstellen
moisture_sensor = ADC(Pin(AOUT_PIN))

#ADC auf 12bit setzen
moisture_sensor.width(ADC.WIDTH_12BIT)

moisture_sensor.atten(ADC.ATTN_11DB)

#Dauerschleife
while True:
    value = moisture_sensor.read()
    
    print("Moisture: {}".format(value)) #Schreibt den aktuellen Wert des Sensors
    
    time.sleep(5) #Pause von 20 Sekunden