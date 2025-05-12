import math
import time
import random
from .base import Sensor

class LightSensor(Sensor):
    def __init__(self, sensor_id, name="LightSensor", min_value=0, max_value=10000, frequency=1):
        super().__init__(sensor_id, name, "lx", min_value, max_value, frequency)
        self._start_time = time.time()

    def _generate_new_value(self): # Implementacja metody abstrakcyjnej
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")
        elapsed = time.time() - self._start_time
        # Symulacja dnia i nocy (sinusoida, przesunięcie fazowe)
        cycle = (math.sin(elapsed / 60 * 2 * math.pi - math.pi / 2) + 1) / 2  # 0 (noc) do 1 (dzień)
        value = self.min_value + (self.max_value - self.min_value) * cycle
        value += random.uniform(-100, 100)
        value = max(self.min_value, min(self.max_value, value))
        return value