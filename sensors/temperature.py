from .base import Sensor

class TemperatureSensor(Sensor):
    def __init__(self, sensor_id):
        super().__init__(sensor_id, "TemperatureSensor", "°C", -20, 50)