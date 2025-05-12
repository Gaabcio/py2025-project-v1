import random
from .base import Sensor

class PressureSensor(Sensor):
    def __init__(self, sensor_id, name="PressureSensor", min_value=950, max_value=1050, frequency=1):
        super().__init__(sensor_id, name, "hPa", min_value, max_value, frequency)

    def _generate_new_value(self): # Implementacja metody abstrakcyjnej
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")
        # Fluktuacje wokół ostatniej wartości
        # Użyj self.last_value z klasy bazowej, jeśli jest dostępne, inaczej wartość startowa
        last = self.last_value if self.last_value is not None else random.uniform(self.min_value, self.max_value)
        value = last + random.uniform(-2, 2)
        value = max(self.min_value, min(self.max_value, value))
        return value