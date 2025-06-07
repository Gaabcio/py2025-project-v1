import time
from datetime import datetime
import sys

from sensors import TemperatureSensor, HumiditySensor, PressureSensor, LightSensor
from logger import Logger
from network.client import NetworkClient
from network.config import load_config


def main():
    # 1. Wczytaj konfigurację sieci z YAML i loggera z JSON
    try:
        net_cfg = load_config("config.yaml")["network"]
        logger_config_path = "config.json"
        logger = Logger(logger_config_path)
        logger.start()
    except FileNotFoundError as e:
        print(f"KRYTYCZNY BŁĄD: Nie znaleziono pliku konfiguracyjnego: {e}. Sprawdź ścieżki i nazwy plików.")
        sys.exit(1)
    except KeyError as e:
        print(f"KRYTYCZNY BŁĄD: Brak klucza w konfiguracji: {e} (sprawdź config.yaml lub config.json).")
        sys.exit(1)
    except Exception as e:
        print(f"KRYTYCZNY BŁĄD podczas inicjalizacji: {e}")
        sys.exit(1)

    # 2. Zainicjuj sensory
    sensors = [
        TemperatureSensor("temp01"),
        HumiditySensor("hum01"),
        PressureSensor("press01"),
        LightSensor("light01")
    ]
    for s in sensors:
        s.register_callback(logger.log_reading)
        s.start()

    # 3. Zainicjuj i połącz klienta sieciowego
    client = NetworkClient(
        host=net_cfg["host"],
        port=int(net_cfg["port"]),  # Upewnij się, że port jest int
        timeout=float(net_cfg.get("timeout", 5.0)),  # Użyj .get i konwertuj na float
        retries=int(net_cfg.get("retries", 3)),  # Użyj .get i konwertuj na int
        logger=logger
    )

    try:
        print(f"Attempting to connect to server at {net_cfg['host']}:{net_cfg['port']}...")
        client.connect()

    except Exception as e:
        print(f"CRITICAL: Failed to connect to network server: {e}. Exiting.")

        logger.log_reading("startup", datetime.now(), 0, f"client_connect_failed: {type(e).__name__}")
        logger.stop()
        sys.exit(1)

    # 4. Pętla do cyklicznego odczytu i wysyłki
    def sensor_loop():
        try:
            while True:

                for sensor in sensors:
                    value = sensor.read_value()
                    if value is not None:
                        data_payload = {
                            "timestamp": datetime.now().isoformat(),
                            "sensor_id": sensor.sensor_id,
                            "value": value,
                            "unit": sensor.unit
                        }
                        print(f"Odczyt: {data_payload['sensor_id']} = {data_payload['value']} {data_payload['unit']}")

                        if not client.send(data_payload):
                            print(
                                f"ALERT: Failed to send data for sensor {sensor.sensor_id} after all retries. Check server and network.")

                time.sleep(1)
        except KeyboardInterrupt:
            print("\nSensor loop interrupted by user.")
        except Exception as e:
            print(f"ERROR in sensor_loop: {e}")
            if logger:
                logger.log_reading("main_loop", datetime.now(), 0, f"sensor_loop_error: {type(e).__name__}")
        finally:
            print("Closing network client and logger...")
            if client:
                client.close()
            if logger:
                logger.stop()
            print("Cleanup finished.")

    sensor_loop()


if __name__ == "__main__":
    main()