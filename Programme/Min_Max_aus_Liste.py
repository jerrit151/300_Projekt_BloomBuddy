import time

# Liste zum Speichern der Messwerte
fuellstand_roh = []

# 10 Messwerte aufnehmen
for i in range(10):
    fuellstand_roh.append(tof_sensor.read())
    time.sleep(0.1)  # Kurze Pause zwischen den Messungen

# Höchsten und niedrigsten Wert entfernen
fuellstand_roh.remove(max(fuellstand_roh))  # Entfernt den höchsten Wert
fuellstand_roh.remove(min(fuellstand_roh))  # Entfernt den niedrigsten Wert

# Messwerte in der Liste kontrollieren
print(fuellstand_roh)

# Mittelwert berechnen
fuellstand = round(sum(fuellstand_roh) / len(fuellstand_roh))

print(f"Entfernung: {fuellstand} mm")
