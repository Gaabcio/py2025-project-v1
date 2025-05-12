from sensors import TemperatureSensor, HumiditySensor, PressureSensor, LightSensor
from logger import Logger
import time

def main():
    # Inicjalizacja loggera
    logger = Logger("config.json")
    logger.start()

    # Tworzenie czujników
    sensors = [
        TemperatureSensor(sensor_id="temp1"),
        HumiditySensor(sensor_id="hum1"),
        PressureSensor(sensor_id="press1"),
        LightSensor(sensor_id="light1")
    ]

    # Rejestracja loggera jako callbacka dla każdego czujnika
    for sensor in sensors:
        sensor.register_callback(logger.log_reading)

    # Symulacja odczytów
    try:
        for i in range(5):  # 10 cykli odczytów
            print(f"=== Odczyty {i+1} ===")
            for sensor in sensors:
                value = sensor.read_value()
                print(f"{sensor.name}: {value:.2f} {sensor.unit}")
            print()
            time.sleep(1)  # Czekaj 1 sekundę między odczytami
    finally:
        # Zatrzymanie loggera
        logger.stop()

if __name__ == "__main__":
    main()