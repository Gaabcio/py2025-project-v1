import random
from .base import Sensor

class HumiditySensor(Sensor):
    def __init__(self, sensor_id, name="HumiditySensor", min_value=0, max_value=100, frequency=1):
        super().__init__(sensor_id, name, "%", min_value, max_value, frequency)

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")
        # Losowa zmienność + powolny trend
        trend = random.uniform(-5, 5)
        last = self.last_value if self.last_value is not None else random.uniform(self.min_value, self.max_value)
        value = last + trend
        value = max(self.min_value, min(self.max_value, value))
        value += random.uniform(-2, 2)
        value = max(self.min_value, min(self.max_value, value))
        self.last_value = value
        self._add_to_history(value)
        return value