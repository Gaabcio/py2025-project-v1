from .base import Sensor

class LightSensor(Sensor):
    def __init__(self, sensor_id):
        super().__init__(sensor_id, "LightSensor", "lx", 0, 10000)