import time

from sensors import TemperatureSensor, HumiditySensor, PressureSensor, LightSensor

sensors = [
    TemperatureSensor(sensor_id=1),
    HumiditySensor(sensor_id=2),
    PressureSensor(sensor_id=3),
    LightSensor(sensor_id=4)
]

for i in range(5):
    print(f"=== Odczyty {i+1} ===")
    for sensor in sensors:
        value = sensor.read_value()
        print(f"{sensor.name}: {value:.2f} {sensor.unit}")
    print()
    time.sleep(1)