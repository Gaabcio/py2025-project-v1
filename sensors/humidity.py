from .base import Sensor

class HumiditySensor(Sensor):
    def __init__(self, sensor_id):
        super().__init__(sensor_id, "HumiditySensor", "%", 0, 100)