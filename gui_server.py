import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from datetime import datetime, timedelta
import json
import os
from collections import deque
import queue

from server.server import NetworkServer

GUI_CONFIG_FILE = "gui_config.json"
MAX_DATA_AGE_SECONDS = 12 * 60 * 60
DATA_POINTS_LIMIT_PER_SENSOR = 5000


class SensorDataStore:
    def __init__(self):

        self.sensor_readings = {}
        self.sensor_metadata = {}

    def add_reading(self, sensor_id, timestamp_dt, value, unit):
        if sensor_id not in self.sensor_readings:
            self.sensor_readings[sensor_id] = deque(maxlen=DATA_POINTS_LIMIT_PER_SENSOR)


        now = datetime.now()
        if self.sensor_readings[sensor_id]:
            while self.sensor_readings[sensor_id] and \
                    (now - self.sensor_readings[sensor_id][0][0]).total_seconds() > MAX_DATA_AGE_SECONDS:
                self.sensor_readings[sensor_id].popleft()

        self.sensor_readings[sensor_id].append((timestamp_dt, float(value)))

        if sensor_id not in self.sensor_metadata:
            self.sensor_metadata[sensor_id] = {}
        self.sensor_metadata[sensor_id]['unit'] = unit
        self.sensor_metadata[sensor_id]['last_value'] = float(value)
        self.sensor_metadata[sensor_id]['last_timestamp_dt'] = timestamp_dt

    def get_last_reading(self, sensor_id):
        if sensor_id in self.sensor_metadata and 'last_value' in self.sensor_metadata[sensor_id]:
            meta = self.sensor_metadata[sensor_id]
            return {
                "value": meta['last_value'],
                "unit": meta.get('unit', ''),
                "timestamp": meta['last_timestamp_dt']
            }
        return None

    def calculate_average(self, sensor_id, timespan_seconds):
        if sensor_id not in self.sensor_readings:
            return None

        relevant_readings = []
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=timespan_seconds)


        for ts, val in list(self.sensor_readings[sensor_id]):
            if ts >= cutoff_time:
                relevant_readings.append(val)

        if not relevant_readings:
            return None
        return sum(relevant_readings) / len(relevant_readings)

    def get_all_sensor_ids(self):
        return list(self.sensor_readings.keys())


class ServerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sensor Network Server GUI")
        self.geometry("800x600")

        self.port_var = tk.StringVar(value=self._load_gui_config().get("last_port", "9999"))
        self.server_instance = None
        self.server_thread = None
        self.data_store = SensorDataStore()
        self.message_queue = queue.Queue()

        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.after(100, self._process_message_queue)
        self.after(1200, self._periodic_table_update)

    def _load_gui_config(self):
        if os.path.exists(GUI_CONFIG_FILE):
            try:
                with open(GUI_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_gui_config(self):
        config = {"last_port": self.port_var.get()}
        try:
            with open(GUI_CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except IOError:
            self.update_status("Error saving GUI configuration.", "red")

    def _create_widgets(self):
        # Top panel for controls
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top_frame, text="Server Port:").pack(side=tk.LEFT, padx=(0, 5))
        self.port_entry = ttk.Entry(top_frame, textvariable=self.port_var, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=(0, 10))

        self.start_button = ttk.Button(top_frame, text="Start Server", command=self._start_server)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        self.stop_button = ttk.Button(top_frame, text="Stop Server", command=self._stop_server, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)

        table_frame = ttk.Frame(self, padding="10")
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        columns = ("sensor_id", "last_value", "unit", "timestamp", "avg_1h", "avg_12h")
        self.sensor_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.sensor_table.heading("sensor_id", text="Sensor ID")
        self.sensor_table.heading("last_value", text="Last Value")
        self.sensor_table.heading("unit", text="Unit")
        self.sensor_table.heading("timestamp", text="Timestamp")
        self.sensor_table.heading("avg_1h", text="Avg (1h)")
        self.sensor_table.heading("avg_12h", text="Avg (12h)")

        self.sensor_table.column("sensor_id", width=100, anchor=tk.W)
        self.sensor_table.column("last_value", width=100, anchor=tk.E)
        self.sensor_table.column("unit", width=50, anchor=tk.CENTER)
        self.sensor_table.column("timestamp", width=150, anchor=tk.CENTER)
        self.sensor_table.column("avg_1h", width=100, anchor=tk.E)
        self.sensor_table.column("avg_12h", width=100, anchor=tk.E)


        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.sensor_table.yview)
        self.sensor_table.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sensor_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


        self.status_bar = ttk.Label(self, text="Server stopped.", padding="5", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message, color="black"):
        self.status_bar.config(text=message, foreground=color)

    def _server_data_handler(self, data_dict):

        self.message_queue.put(data_dict)

    def _process_message_queue(self):
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()

                if message["type"] == "sensor_data":
                    payload = message["payload"]
                    sensor_id = payload.get("sensor_id")
                    timestamp_str = payload.get("timestamp")
                    value = payload.get("value")
                    unit = payload.get("unit")

                    if all([sensor_id, timestamp_str, value is not None, unit]):
                        try:
                            timestamp_dt = datetime.fromisoformat(timestamp_str)
                            self.data_store.add_reading(sensor_id, timestamp_dt, value, unit)

                        except ValueError:
                            print(f"GUI: Error parsing timestamp {timestamp_str}")
                        except Exception as e:
                            print(f"GUI: Error processing sensor data: {e}")
                elif message["type"] == "server_error":
                    self.update_status(f"SERVER ERROR: {message['message']}", "red")
                    self._server_stopped_ui_state()
                elif message["type"] == "decode_error":
                    self.update_status(f"SERVER: {message['message']}", "orange")


        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_message_queue)

    def _start_server(self):
        if self.server_instance and self.server_instance.running:
            messagebox.showwarning("Server Control", "Server is already running.")
            return

        port_str = self.port_var.get()
        try:
            port = int(port_str)
            if not (1024 <= port <= 65535):
                raise ValueError("Port must be between 1024 and 65535.")
        except ValueError as e:
            messagebox.showerror("Invalid Port", f"Error: {e}")
            return

        self.update_status(f"Starting server on port {port}...", "blue")


        self.server_instance = NetworkServer(port, data_callback=self._server_data_handler)

        self.server_thread = threading.Thread(target=self.server_instance.start, daemon=True)
        self.server_thread.start()

        self.after(1000, self._check_server_startup_status)

        self._save_gui_config()

    def _check_server_startup_status(self):
        if self.server_instance and self.server_instance.running:
            self.update_status(f"Server listening on port {self.server_instance.port}.", "green")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.DISABLED)
        elif self.server_instance:
            if "SERVER ERROR" not in self.status_bar.cget("text"):
                self.update_status("Server failed to start. Check console.", "red")
            self._server_stopped_ui_state()

    def _stop_server(self):
        if self.server_instance and self.server_instance.running:
            self.update_status("Stopping server...", "blue")
            self.server_instance.stop()


            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=2.0)

            if self.server_thread and not self.server_thread.is_alive():
                self.update_status("Server stopped.", "black")
            else:
                self.update_status("Server stop requested. May take a moment or timed out.", "orange")

        else:
            self.update_status("Server is not running.", "black")

        self._server_stopped_ui_state()
        self.server_instance = None

    def _server_stopped_ui_state(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.NORMAL)

    def _periodic_table_update(self):
        self._update_sensor_table()
        self.after(1200, self._periodic_table_update)

    def _update_sensor_table(self):
        for item in self.sensor_table.get_children():
            self.sensor_table.delete(item)

        sensor_ids = self.data_store.get_all_sensor_ids()
        sensor_ids.sort()

        for sensor_id in sensor_ids:
            last_reading = self.data_store.get_last_reading(sensor_id)
            if not last_reading:
                continue

            avg_1h = self.data_store.calculate_average(sensor_id, 3600)
            avg_12h = self.data_store.calculate_average(sensor_id, 12 * 3600)

            self.sensor_table.insert("", tk.END, values=(
                sensor_id,
                f"{last_reading['value']:.2f}" if isinstance(last_reading['value'], float) else last_reading['value'],
                last_reading['unit'],
                last_reading['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                f"{avg_1h:.2f}" if avg_1h is not None else "N/A",
                f"{avg_12h:.2f}" if avg_12h is not None else "N/A"
            ))

    def _on_closing(self):
        if self.server_instance and self.server_instance.running:
            if messagebox.askokcancel("Quit", "Server is running. Do you want to stop the server and quit?"):
                self._stop_server()
                self.destroy()
            else:
                return
        else:
            self.destroy()


if __name__ == "__main__":

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    app = ServerGUI()
    app.mainloop()