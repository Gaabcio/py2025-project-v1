import random
import time
from datetime import datetime

class Sensor:
    def __init__(self, sensor_id, name, unit, min_value, max_value, frequency=1):
        """
        Inicjalizacja czujnika.

        :param sensor_id: Unikalny identyfikator czujnika
        :param name: Nazwa lub opis czujnika
        :param unit: Jednostka miary (np. '°C', '%', 'hPa', 'lux')
        :param min_value: Minimalna wartość odczytu
        :param max_value: Maksymalna wartość odczytu
        :param frequency: Częstotliwość odczytów (sekundy)
        """
        self.sensor_id = sensor_id
        self.name = name
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.frequency = frequency
        self.active = True
        self.last_value = None
        self._callbacks = []

    def read_value(self):
        """
        Symuluje pobranie odczytu z czujnika.
        W klasie bazowej zwraca losową wartość z przedziału [min_value, max_value].
        """
        if not self.active:
            # Zamiast rzucać wyjątek, można zwrócić None lub specjalną wartość
            # print(f"Czujnik {self.name} jest wyłączony.")
            return None

        value = random.uniform(self.min_value, self.max_value)
        self.last_value = value
        timestamp = datetime.now()
        for callback in self._callbacks:
            callback(self.sensor_id, timestamp, value, self.unit)
        return value

    def calibrate(self, calibration_factor):
        """
        Kalibruje ostatni odczyt przez przemnożenie go przez calibration_factor.
        Jeśli nie wykonano jeszcze odczytu, wykonuje go najpierw.
        """
        if self.last_value is None:
            self.read_value()
        
        if self.last_value is not None: # Dodatkowe sprawdzenie, czy read_value() coś zwróciło
            self.last_value *= calibration_factor
        return self.last_value

    def get_last_value(self):
        """
        Zwraca ostatnią wygenerowaną wartość, jeśli była wygenerowana.
        """
        if self.last_value is None:
            return self.read_value()
        return self.last_value

    def start(self):
        """
        Włącza czujnik.
        """
        self.active = True

    def stop(self):
        """
        Wyłącza czujnik.
        """
        self.active = False

    def register_callback(self, callback):
        """
        Rejestruje funkcję zwrotną (callback), która będzie wywoływana po odczycie wartości.
        """
        if callable(callback):
            self._callbacks.append(callback)
        else:
            print(f"Błąd: Przekazany obiekt nie jest funkcją (callable).")


    def __str__(self):
        return f"Sensor(id={self.sensor_id}, name='{self.name}', unit='{self.unit}')"

class TemperatureSensor(Sensor):
    def __init__(self, sensor_id, name="Czujnik Temperatury", unit="°C", min_value=-20, max_value=50, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)

    def read_value(self):
        """
        Symuluje odczyt temperatury.
        Można tu dodać logikę np. symulującą dobowe wahania temperatury.
        """
        if not self.active:
            # print(f"Czujnik {self.name} jest wyłączony.")
            return None
        # Prosta symulacja - losowa wartość w zakresie
        value = random.uniform(self.min_value, self.max_value)
        # Dodanie niewielkiej losowej zmiany w stosunku do poprzedniej wartości, jeśli istnieje
        if self.last_value is not None:
            change = random.uniform(-0.5, 0.5) # Niewielka zmiana
            value = max(self.min_value, min(self.max_value, self.last_value + change))
        else:
            value = random.uniform(self.min_value, self.max_value)

        self.last_value = round(value, 2) # Zaokrąglenie do 2 miejsc po przecinku
        timestamp = datetime.now()
        for callback in self._callbacks:
            callback(self.sensor_id, timestamp, self.last_value, self.unit)
        return self.last_value

class HumiditySensor(Sensor):
    def __init__(self, sensor_id, name="Czujnik Wilgotności", unit="%", min_value=0, max_value=100, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)

    def read_value(self):
        """
        Symuluje odczyt wilgotności.
        """
        if not self.active:
            # print(f"Czujnik {self.name} jest wyłączony.")
            return None
        # Prosta symulacja
        value = random.uniform(self.min_value, self.max_value)
        if self.last_value is not None:
            change = random.uniform(-2, 2) # Wilgotność może się zmieniać nieco szybciej
            value = max(self.min_value, min(self.max_value, self.last_value + change))
        else:
            value = random.uniform(self.min_value, self.max_value)
        
        self.last_value = round(value, 1) # Zaokrąglenie do 1 miejsca po przecinku
        timestamp = datetime.now()
        for callback in self._callbacks:
            callback(self.sensor_id, timestamp, self.last_value, self.unit)
        return self.last_value

class PressureSensor(Sensor):
    def __init__(self, sensor_id, name="Czujnik Ciśnienia", unit="hPa", min_value=950, max_value=1050, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)

    def read_value(self):
        """
        Symuluje odczyt ciśnienia atmosferycznego.
        """
        if not self.active:
            # print(f"Czujnik {self.name} jest wyłączony.")
            return None
        # Ciśnienie zmienia się powoli
        value = random.uniform(self.min_value, self.max_value)
        if self.last_value is not None:
            change = random.uniform(-0.2, 0.2) 
            value = max(self.min_value, min(self.max_value, self.last_value + change))
        else:
            value = random.uniform(self.min_value, self.max_value)

        self.last_value = round(value, 2)
        timestamp = datetime.now()
        for callback in self._callbacks:
            callback(self.sensor_id, timestamp, self.last_value, self.unit)
        return self.last_value

class LightSensor(Sensor):
    def __init__(self, sensor_id, name="Czujnik Natężenia Światła", unit="lx", min_value=0, max_value=10000, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)

    def read_value(self):
        """
        Symuluje odczyt natężenia światła.
        Można tu dodać logikę symulującą zmiany w zależności od pory dnia.
        """
        if not self.active:
            # print(f"Czujnik {self.name} jest wyłączony.")
            return None
        # Prosta symulacja, np. w zależności od godziny (uproszczona)
        current_hour = datetime.now().hour
        if 6 <= current_hour < 8: # Poranek
            val = random.uniform(50, 500)
        elif 8 <= current_hour < 18: # Dzień
            val = random.uniform(500, self.max_value)
        elif 18 <= current_hour < 20: # Wieczór
            val = random.uniform(50, 500)
        else: # Noc
            val = random.uniform(self.min_value, 50)
        
        self.last_value = round(val, 0)
        timestamp = datetime.now()
        for callback in self._callbacks:
            callback(self.sensor_id, timestamp, self.last_value, self.unit)
        return self.last_value

if __name__ == '__main__':
    # Przykładowe użycie
    temp_sensor = TemperatureSensor(sensor_id="temp001", frequency=2)
    humidity_sensor = HumiditySensor(sensor_id="hum001", frequency=3)
    pressure_sensor = PressureSensor(sensor_id="press001", frequency=5)
    light_sensor = LightSensor(sensor_id="light001", frequency=1.5)

    sensors = [temp_sensor, humidity_sensor, pressure_sensor, light_sensor]

    print("Uruchamianie symulacji czujników...")
    for sensor in sensors:
        sensor.start()
        print(f"Uruchomiono: {sensor}")

    try:
        for i in range(10): # Symuluj przez 10 odczytów dla każdego (w przybliżeniu)
            for sensor in sensors:
                # Symulacja odczytu zgodna z częstotliwością (uproszczone)
                # W rzeczywistym systemie każdy czujnik działałby we własnym wątku lub pętli zdarzeń
                # Tutaj dla prostoty wywołujemy read_value() sekwencyjnie,
                # ale logger będzie wywoływany przez callback.
                # Dla demonstracji callbacków, log_reading zostanie dodane w module loggera.
                
                # Prosta symulacja opóźnienia zgodnego z frequency
                # time.sleep(sensor.frequency) # To zablokowałoby pętlę, nie jest idealne tutaj
                
                # W tym miejscu odczyt jest inicjowany, a callback (jeśli zarejestrowany) zostanie wywołany wewnątrz read_value()
                value = sensor.read_value()
                if value is not None:
                    print(f"Odczyt z {sensor.name} ({sensor.sensor_id}): {value} {sensor.unit} o {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"Czujnik {sensor.name} ({sensor.sensor_id}) jest wyłączony lub nie udało się odczytać wartości.")
            print("-" * 20)
            time.sleep(1) # Główna pętla symulacji robi pauzę

    except KeyboardInterrupt:
        print("\nZatrzymywanie symulacji...")
    finally:
        for sensor in sensors:
            sensor.stop()
            print(f"Zatrzymano: {sensor}")