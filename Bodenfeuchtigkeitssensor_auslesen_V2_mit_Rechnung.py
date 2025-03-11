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
from machine import Pin, ADC
import time

#Ausgangs-Pin für das Relais definieren
relais_in1 = Pin(3, Pin.OUT)

# ADC-Pin für den Sensor
soil_pin = Pin(5)
soil_adc = ADC(soil_pin)

# ADC-Einstellungen
soil_adc.atten(ADC.ATTN_11DB)  # Vollbereich: 3.3V
soil_adc.width(ADC.WIDTH_12BIT)  # Bereich: 0 bis 4095

# Kalibrierwerte
dry_value = 0  # Trockener Boden
wet_value = 100  # Nasser Boden

# ADC-Werte für trockenen und nassen Boden (müssen experimentell ermittelt werden)
# Hier sind Platzhalter, ersetzen Sie diese durch die tatsächlichen ADC-Werte
dry_adc_value = 3070  # Beispielwert für trockenen Boden, reagiert sehr empfindlich auf kleine Änderungen mit diesem Wert in der Luft ca.2%
wet_adc_value = 1700  # Beispielwert für nassen Boden

while True:
        # Sensorwert lesen
        soil_adc_value = soil_adc.read()
        
        # Berechnung des Feuchtigkeitswertes basierend auf den Kalibrierwerten
        moisture_percentage = ((soil_adc_value - wet_adc_value) / (dry_adc_value - wet_adc_value)) * (dry_value - wet_value) + wet_value
        
        # Sicherstellen, dass der Wert im Bereich von 0 bis 100 bleibt
        moisture_percentage = max(0, min(moisture_percentage, 100))
        
        print(f'Soil Moisture: {moisture_percentage:.1f}%')
        
        #Fällt die Bodenfeuchtigkeit unter 20% soll das Relais der Pumpe angesteuert werden
        if moisture_percentage <= 20:
            relais_in1.value(1) #Ausgang auf TRUE setzen
            print("Relais angesteuert, Pumpe ein")
        else:
            relais_in1.value(0) #Ist die Bodefeuchtigkeit nicht unter 20% bleibt das Relais und die Pumpe aus
            print("Relais nicht angesteuert, Pumpe aus")
            
        time.sleep(10)  # Wartezeit zwischen den Messungen