import random
import datetime
from abc import ABC, abstractmethod # Dodano import

class Sensor(ABC): # Sensor dziedziczy po ABC (Abstract Base Class)
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
        self.history = []
        self.callbacks = []

    def register_callback(self, callback):
        """
        Rejestruje callback do wywołania przy odczycie danych.
        """
        self.callbacks.append(callback)

    @abstractmethod
    def _generate_new_value(self):
        """
        Metoda abstrakcyjna, którą klasy potomne muszą zaimplementować.
        Odpowiada za wygenerowanie nowej wartości specyficznej dla danego typu czujnika.
        Powinna zwrócić wygenerowaną wartość.
        """
        pass

    def read_value(self):
        """
        Odczytuje wartość z czujnika, aktualizuje stan wewnętrzny i powiadamia callbacki.
        """
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        # Pobranie wartości z implementacji w klasie potomnej
        value = self._generate_new_value()

        self.last_value = value
        self._add_to_history(value) # Dodanie do historii

        # Wywołanie callbacków
        timestamp = datetime.datetime.now() # Pobranie aktualnego znacznika czasu
        for callback in self.callbacks:
            callback(self.sensor_id, timestamp, value, self.unit)

        return value

    def calibrate(self, calibration_factor):
        """
        Kalibruje ostatni odczyt przez przemnożenie go przez calibration_factor.
        Jeśli nie wykonano jeszcze odczytu, wykonuje go najpierw.
        """
        if self.last_value is None:
            self.read_value() # To wywoła _generate_new_value, callbacki, historię
        self.last_value *= calibration_factor
        # Uwaga: skalibrowana wartość jest dodawana do historii, ale callbacki nie są ponownie
        # wywoływane z tą skalibrowaną wartością w ramach tej metody.
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