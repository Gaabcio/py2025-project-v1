import csv
import json
import os
import shutil
import zipfile
from datetime import datetime, timedelta
from typing import Optional, Iterator, Dict

class Logger:
    def __init__(self, config_path: str):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"KRYTYCZNY BŁĄD Loggera: Plik konfiguracyjny '{config_path}' nie został znaleziony.")
            raise
        except json.JSONDecodeError:
            print(f"KRYTYCZNY BŁĄD Loggera: Nieprawidłowy format JSON w pliku '{config_path}'.")
            raise

        self.log_dir = config.get("log_dir", "./logs")
        self.filename_pattern = config.get("filename_pattern", "sensors_%Y%m%d.csv")
        self.buffer_size = config.get("buffer_size", 100)
        self.rotate_every_hours = config.get("rotate_every_hours")
        self.max_size_mb = config.get("max_size_mb")
        self.rotate_after_lines = config.get("rotate_after_lines")
        self.retention_days = config.get("retention_days")

        self.archive_dir = os.path.join(self.log_dir, "archive")
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            os.makedirs(self.archive_dir, exist_ok=True)
        except OSError as e:
            print(f"KRYTYCZNY BŁĄD Loggera: Nie można utworzyć katalogów logów '{self.log_dir}' lub archiwum '{self.archive_dir}': {e}")
            raise

        self._buffer = []
        self._current_file_path = None
        self._file_handle = None
        self._file_creation_time = None
        self._file_line_count = 0
        self.is_active = False
        self._last_closed_file_path = None

    def _get_new_filepath(self) -> str:
        return os.path.join(self.log_dir, datetime.now().strftime(self.filename_pattern))

    def start(self) -> None:
        if self.is_active:
            return

        self._current_file_path = self._get_new_filepath()
        file_exists = os.path.exists(self._current_file_path)
        
        try:
            self._file_handle = open(self._current_file_path, 'a+', newline='', encoding='utf-8')
            self._file_creation_time = datetime.now()
            self._file_line_count = 0
            if not file_exists or os.path.getsize(self._current_file_path) == 0:
                writer = csv.writer(self._file_handle)
                writer.writerow(["timestamp", "sensor_id", "value", "unit"])
                self._file_handle.flush()

        except IOError as e:
            print(f"BŁĄD Loggera: Nie można otworzyć pliku logu '{self._current_file_path}': {e}")
            self._current_file_path = None
            self._file_handle = None
            return
            
        self.is_active = True

    def stop(self) -> None:
        if not self.is_active:
            return
            
        self._flush_buffer()
        if self._file_handle:
            try:
                self._last_closed_file_path = self._current_file_path
                self._file_handle.close()
            except IOError:
                pass
        
        self._file_handle = None
        self.is_active = False

    def _flush_buffer(self) -> None:
        if not self._file_handle or self._file_handle.closed:
            return
        if self._buffer:
            try:
                writer = csv.writer(self._file_handle)
                writer.writerows(self._buffer)
                self._file_handle.flush() 
                self._file_line_count += len(self._buffer)
                self._buffer.clear()
            except IOError:
                pass

    def log_reading(
        self,
        sensor_id: str,
        timestamp: datetime, 
        value: float,
        unit: str
    ) -> None:

        if sensor_id == "network":
            return

        if not self.is_active or not self._file_handle:
            return

        formatted_timestamp = timestamp.isoformat()
        self._buffer.append([formatted_timestamp, sensor_id, value, unit])

        if len(self._buffer) >= self.buffer_size:
            self._flush_buffer()
        
        self._check_rotation()

    def _check_rotation(self) -> None:
        if not self._current_file_path or not self.is_active or not self._file_handle:
            return

        perform_rotation = False
        
        if self.rotate_every_hours and self._file_creation_time:
            if datetime.now() >= self._file_creation_time + timedelta(hours=self.rotate_every_hours):
                perform_rotation = True
        
        if not perform_rotation and self.max_size_mb:
            try:
                self._flush_buffer()
                if self._file_handle and not self._file_handle.closed:
                     if os.path.getsize(self._current_file_path) >= self.max_size_mb * 1024 * 1024:
                        perform_rotation = True
            except OSError: 
                pass

        if not perform_rotation and self.rotate_after_lines:
            if self._file_line_count >= self.rotate_after_lines:
                perform_rotation = True

        if perform_rotation:
            self._rotate()

    def _rotate(self) -> None:
        old_file_path_for_archive = self._current_file_path
        self.stop() 

        if old_file_path_for_archive and os.path.exists(old_file_path_for_archive):
            archive_filename_original = os.path.basename(old_file_path_for_archive)
            archive_base, archive_ext = os.path.splitext(archive_filename_original)
            
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S%f")
            zip_filename = f"{archive_base}_{timestamp_str}{archive_ext}.zip"
            zip_filepath = os.path.join(self.archive_dir, zip_filename)

            try:
                with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(old_file_path_for_archive, archive_filename_original)
                os.remove(old_file_path_for_archive) 
            except (IOError, OSError, zipfile.BadZipFile):
                pass
        
        self._clean_old_archives()
        self.start()

    def _clean_old_archives(self) -> None:
        if not self.retention_days or self.retention_days <= 0:
            return

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        for filename in os.listdir(self.archive_dir):
            if filename.endswith(".zip"):
                filepath = os.path.join(self.archive_dir, filename)
                try:
                    file_mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_mod_time < cutoff_date:
                        os.remove(filepath)
                except OSError:
                    pass 

    def read_logs(
        self,
        start_dt: datetime,
        end_dt: datetime,
        sensor_id: Optional[str] = None
    ) -> Iterator[Dict]:
        files_to_check = set()

        if self.is_active and self._current_file_path and os.path.exists(self._current_file_path):
            files_to_check.add(self._current_file_path)
        if self._last_closed_file_path and os.path.exists(self._last_closed_file_path):
            files_to_check.add(self._last_closed_file_path)

        try:
            for filename in os.listdir(self.log_dir):
                if filename.endswith(".csv"):
                    filepath = os.path.join(self.log_dir, filename)
                    files_to_check.add(filepath)
        except OSError:
            return

        archive_files_content = {} 
        try:
            for filename in os.listdir(self.archive_dir):
                if filename.endswith(".zip"):
                    zip_filepath = os.path.join(self.archive_dir, filename)
                    try:
                        with zipfile.ZipFile(zip_filepath, 'r') as zf:
                            if not zf.namelist(): continue
                            csv_filename_in_zip = zf.namelist()[0] 
                            archive_files_content[zip_filepath] = zf.read(csv_filename_in_zip).decode('utf-8').splitlines()
                    except (zipfile.BadZipFile, IndexError, UnicodeDecodeError):
                        pass 
        except OSError:
            pass


        for filepath in list(files_to_check): 
            try:
                if self.is_active and filepath == self._current_file_path:
                    self._flush_buffer()

                with open(filepath, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            ts_str = row.get("timestamp")
                            if not ts_str: continue
                            try:
                                record_ts = datetime.fromisoformat(ts_str)
                            except ValueError:
                                record_ts = datetime.strptime(ts_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                            
                            if start_dt <= record_ts <= end_dt:
                                if sensor_id is None or row.get("sensor_id") == sensor_id:
                                    try:
                                        row["value"] = float(row["value"])
                                    except (ValueError, TypeError): pass 
                                    row["timestamp"] = record_ts 
                                    yield row
                        except (csv.Error, ValueError, TypeError): pass
            except IOError: pass
            except Exception: pass

        for zip_filepath, lines in archive_files_content.items():
            if not lines or len(lines) < 2: continue
            
            header_line = lines[0]
            expected_headers = ["timestamp", "sensor_id", "value", "unit"]
            actual_headers = [h.strip() for h in header_line.split(',')]
            
            if not all(eh in actual_headers for eh in expected_headers): continue

            reader = csv.DictReader(lines[1:], fieldnames=actual_headers)
            for row in reader:
                try:
                    ts_str = row.get("timestamp")
                    if not ts_str: continue
                    try:
                        record_ts = datetime.fromisoformat(ts_str)
                    except ValueError:
                         record_ts = datetime.strptime(ts_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')

                    if start_dt <= record_ts <= end_dt:
                        if sensor_id is None or row.get("sensor_id") == sensor_id:
                            try:
                                row["value"] = float(row["value"])
                            except (ValueError, TypeError):
                                pass
                            row["timestamp"] = record_ts
                            yield row
                except (csv.Error, ValueError, TypeError):
                    pass

                except Exception:
                    pass