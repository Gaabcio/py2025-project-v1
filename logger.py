import os
import csv
import json
import datetime
import zipfile
from typing import Optional, Dict, Iterator

class Logger:
    def __init__(self, config_path: str):
        """
        Inicjalizuje logger na podstawie pliku JSON.
        :param config_path: Ścieżka do pliku konfiguracyjnego (.json)
        """
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.log_dir = config.get("log_dir", "./logs")
        self.filename_pattern = config.get("filename_pattern", "sensors_%Y%m%d.csv")
        self.buffer_size = config.get("buffer_size", 200)
        self.rotate_every_hours = config.get("rotate_every_hours", 24)
        self.max_size_mb = config.get("max_size_mb", 10)
        self.rotate_after_lines = config.get("rotate_after_lines", 100000)
        self.retention_days = config.get("retention_days", 30)

        self.buffer = []
        self.current_file = None
        self.current_writer = None
        self.last_rotation = datetime.datetime.now()

        # Upewnij się, że katalogi istnieją
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(os.path.join(self.log_dir, "archive"), exist_ok=True)

    def start(self) -> None:
        """
        Otwiera nowy plik CSV do logowania. Jeśli plik jest nowy, zapisuje nagłówek.
        """
        self._rotate_if_needed()

        filename = self._generate_filename()
        self.current_file = open(filename, mode='a', newline='', encoding='utf-8')
        self.current_writer = csv.writer(self.current_file)

        # Jeśli plik jest pusty, zapisz nagłówek
        if self.current_file.tell() == 0:
            self.current_writer.writerow(["timestamp", "sensor_id", "value", "unit"])

    def stop(self) -> None:
        """
        Wymusza zapis bufora i zamyka bieżący plik.
        """
        self._flush_buffer()  # Wymusza zapis bufora do pliku
        if self.current_file:
            self.current_file.close()
            self.current_file = None

    def log_reading(self, sensor_id: str, timestamp: datetime.datetime, value: float, unit: str) -> None:
        """
        Dodaje wpis do bufora i ewentualnie wykonuje rotację pliku.
        """
        self.buffer.append([timestamp.isoformat(), sensor_id, value, unit])  # Dodaj odczyt do bufora

        if len(self.buffer) >= self.buffer_size:  # Sprawdź, czy bufor osiągnął maksymalny rozmiar
            self._flush_buffer()

        self._rotate_if_needed()  # Sprawdź, czy potrzebna jest rotacja pliku

    def read_logs(self, start: datetime.datetime, end: datetime.datetime, sensor_id: Optional[str] = None) -> Iterator[Dict]:
        """
        Pobiera wpisy z logów zadanego zakresu i opcjonalnie konkretnego czujnika.
        """
        for file in self._get_all_log_files():
            with self._open_log_file(file) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_timestamp = datetime.datetime.fromisoformat(row["timestamp"])
                    if start <= row_timestamp <= end and (sensor_id is None or row["sensor_id"] == sensor_id):
                        yield {
                            "timestamp": row_timestamp,
                            "sensor_id": row["sensor_id"],
                            "value": float(row["value"]),
                            "unit": row["unit"]
                        }

    def _flush_buffer(self):
        """
        Zapisuje bufor do pliku.
        """
        if self.current_writer and self.buffer:
            self.current_writer.writerows(self.buffer)  # Zapisz wszystkie wiersze z bufora
            self.buffer = []  # Opróżnij bufor

    def _rotate_if_needed(self):
        """
        Sprawdza, czy potrzebna jest rotacja pliku, i wykonuje ją, jeśli tak.
        """
        if not self.current_file:
            return

        now = datetime.datetime.now()
        file_size_mb = os.path.getsize(self.current_file.name) / (1024 * 1024)

        if (
            (now - self.last_rotation).total_seconds() > self.rotate_every_hours * 3600 or
            file_size_mb >= self.max_size_mb
        ):
            self.stop()
            self._archive_current_file()
            self._clean_old_archives()
            self.last_rotation = now
            self.start()

    def _generate_filename(self) -> str:
        """
        Generuje nazwę pliku na podstawie wzorca.
        """
        now = datetime.datetime.now()
        return os.path.join(self.log_dir, now.strftime(self.filename_pattern))

    def _get_all_log_files(self):
        """
        Zwraca listę wszystkich plików logów (obecnych i archiwalnych).
        """
        logs = [os.path.join(self.log_dir, f) for f in os.listdir(self.log_dir) if f.endswith(".csv")]
        archives = [os.path.join(self.log_dir, "archive", f) for f in os.listdir(os.path.join(self.log_dir, "archive")) if f.endswith(".zip")]
        return logs + archives

    def _open_log_file(self, file: str):
        """
        Otwiera plik logu, zarówno CSV, jak i ZIP.
        """
        if file.endswith(".zip"):
            archive = zipfile.ZipFile(file, 'r')
            csv_name = archive.namelist()[0]
            return archive.open(csv_name, 'r')
        else:
            return open(file, 'r', encoding='utf-8')

    def _archive_current_file(self):
        """
        Archiwizuje bieżący plik logu do katalogu archive/.
        """
        if not self.current_file:
            return

        archive_path = os.path.join(self.log_dir, "archive", os.path.basename(self.current_file.name) + ".zip")
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.write(self.current_file.name, os.path.basename(self.current_file.name))

        os.remove(self.current_file.name)

    def _clean_old_archives(self):
        """
        Usuwa archiwa starsze niż retention_days.
        """
        archive_dir = os.path.join(self.log_dir, "archive")
        for file in os.listdir(archive_dir):
            file_path = os.path.join(archive_dir, file)
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            if (datetime.datetime.now() - file_time).days > self.retention_days:
                os.remove(file_path)