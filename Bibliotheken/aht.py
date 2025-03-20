"""Driver for AHT2x sensors (humidity and temperature):
    Models: AHT20 and AHT21
    I2C Address: 0x38
    Manufacturer website: http://www.aosong.com
"""

import time
from micropython import const

# Autor-Informationen
__author__ = "Jonathan Fromentin, angepasst von ChatGPT"
__credits__ = ["Jonathan Fromentin"]
__license__ = "CeCILL version 2.1"
__version__ = "2.1.0"
__maintainer__ = "Jonathan Fromentin"

# Konstanten
AHT_I2C_ADDR = const(0x38)  # Standard I2C-Adresse für AHT20/AHT21
AHT_STATUS_BUSY = const(0x01)  # Status-Bit für "busy"
AHT_STATUS_CALIBRATED = const(0x10)  # Status-Bit für "calibrated"
AHT_CMD_INIT = const(0xBE)  # Initialisierungsbefehl
AHT_CMD_TRIGGER = const(0xAC)  # Messbefehl
AHT_CMD_RESET = const(0xBA)  # Software-Reset-Befehl

class AHT21:
    """ Klasse für den AHT21-Sensor. """

    def __init__(self, i2c, address=AHT_I2C_ADDR):
        """Initialisiert den AHT21-Sensor."""
        self.i2c = i2c
        self.address = address
        self.temperature = None
        self.humidity = None

        # Warten, bis der Sensor bereit ist
        time.sleep(0.04)  # 40ms nach dem Einschalten warten

        # Kalibrierung durchführen
        self._calibrate()

    def is_calibrated(self):
        """Prüft, ob der Sensor kalibriert ist."""
        status = self._status()
        return bool(status & AHT_STATUS_CALIBRATED)

    def _status(self):
        """Liest das Status-Register des Sensors."""
        try:
            data = bytearray(1)
            self.i2c.readfrom_into(self.address, data)
            return data[0]
        except OSError:
            return AHT_STATUS_BUSY

    def _calibrate(self):
        """Sendet den Initialisierungsbefehl an den Sensor."""
        try:
            self.i2c.writeto(self.address, bytes([AHT_CMD_INIT, 0x08, 0x00]))
            time.sleep(0.01)  # 10ms warten
        except OSError:
            pass

    def reset(self):
        """Setzt den Sensor per Software-Reset zurück."""
        try:
            self.i2c.writeto(self.address, bytes([AHT_CMD_RESET]))
            time.sleep(0.02)  # 20ms für den Reset warten
            self._calibrate()
        except OSError:
            pass

    def measure(self):
        """Führt eine Messung durch und speichert Temperatur und Luftfeuchtigkeit."""
        try:
            # Messbefehl senden
            self.i2c.writeto(self.address, bytes([AHT_CMD_TRIGGER, 0x33, 0x00]))
            time.sleep(0.08)  # 80ms warten

            # Daten lesen
            raw_data = bytearray(6)
            self.i2c.readfrom_into(self.address, raw_data)

            # Daten umwandeln
            raw_hum = (raw_data[1] << 12) | (raw_data[2] << 4) | (raw_data[3] >> 4)
            raw_temp = ((raw_data[3] & 0x0F) << 16) | (raw_data[4] << 8) | raw_data[5]

            # Werte berechnen
            self.humidity = round((raw_hum / 0x100000) * 100, 2)
            self.temperature = round(((raw_temp / 0x100000) * 200) - 50, 2)

            return True
        except OSError:
            self.humidity = None
            self.temperature = None
            return False