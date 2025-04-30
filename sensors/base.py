import random

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
        self.sensor_id = sensor_id          # Unikalny identyfikator czujnika
        self.name = name                    # Nazwa lub opis czujnika
        self.unit = unit                    # Jednostka miary (np. °C, %, hPa, lux)
        self.min_value = min_value          # Minimalna wartość odczytu
        self.max_value = max_value          # Maksymalna wartość odczytu
        self.frequency = frequency          # Częstotliwość odczytów w sekundach
        self.active = True                  # Flaga określająca, czy czujnik jest aktywny
        self.last_value = None              # Ostatnio wygenerowana wartość
        self.history = []                   # Historia ostatnich wartości

    def read_value(self):
        """
        Symuluje pobranie odczytu z czujnika.
        W klasie bazowej zwraca losową wartość z przedziału [min_value, max_value].
        """
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")
        value = random.uniform(self.min_value, self.max_value)
        self.last_value = value
        self._add_to_history(value)
        return value

    def calibrate(self, calibration_factor):
        """
        Kalibruje ostatni odczyt przez przemnożenie go przez calibration_factor.
        Jeśli nie wykonano jeszcze odczytu, wykonuje go najpierw.
        """
        if self.last_value is None:
            self.read_value()
        self.last_value *= calibration_factor
        self._add_to_history(self.last_value)
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

    def _add_to_history(self, value):
        """
        Dodaje wartość do historii odczytów (maks. 100 ostatnich).
        """
        self.history.append(value)
        if len(self.history) > 100:
            self.history.pop(0)

    def get_history(self, n=10):
        """
        Zwraca ostatnie n wartości z historii.
        """
        return self.history[-n:]

    def __str__(self):
        return f"Sensor(id={self.sensor_id}, name={self.name}, unit={self.unit})"