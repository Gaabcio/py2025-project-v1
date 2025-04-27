from .base import Sensor

class PressureSensor(Sensor):
    def __init__(self, sensor_id):
        super().__init__(sensor_id, "PressureSensor", "hPa", 950, 1050)