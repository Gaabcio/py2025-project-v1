import math
import time
import random
from .base import Sensor

class TemperatureSensor(Sensor):
    def __init__(self, sensor_id, name="TemperatureSensor", min_value=-20, max_value=50, frequency=1):
        super().__init__(sensor_id, name, "°C", min_value, max_value, frequency)
        self._start_time = time.time()

    def _generate_new_value(self): # Implementacja metody abstrakcyjnej
        if not self.active: # Chociaż read_value w base to sprawdza, można zostawić dla pewności lub usunąć
            raise Exception(f"Czujnik {self.name} jest wyłączony.")
        # Symulacja cyklu dziennego (sinusoida)
        elapsed = time.time() - self._start_time
        cycle = math.sin(elapsed / 60 * 2 * math.pi)  # cykl 1 min = 1 doba
        base_temp = (self.max_value + self.min_value) / 2
        amplitude = (self.max_value - self.min_value) / 2
        value = base_temp + amplitude * cycle + random.uniform(-1, 1)
        value = max(self.min_value, min(self.max_value, value))
        # Nie ustawiamy już self.last_value ani self._add_to_history tutaj
        return value