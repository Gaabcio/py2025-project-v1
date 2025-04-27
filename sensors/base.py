import random

class Sensor:
    def __init__(self, sensor_id, name, unit, min_value, max_value, frequency=1):
        """
        Unikalny identyfikator, nazwa, jednostka, zakres wartości i częstotliwość.
        """
        self.sensor_id = sensor_id
        self.name = name
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.frequency = frequency
        self.active = True
        self.last_value = None

    def read_value(self):
        """
        Zwraca losową wartość z podanego zakresu.
        """
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")
        value = random.uniform(self.min_value, self.max_value)
        self.last_value = value
        return value

    def get_last_value(self):
        """
        Zwraca ostatnią wygenerowaną wartość.
        """
        return self.last_value

    def start(self):
        self.active = True

    def stop(self):
        self.active = False