import socket
import threading
import json
import sys
import os


# --- Początek definicji klasy NetworkServer ---
class NetworkServer:
    def __init__(self, port: int, data_callback=None):
        self.port = port
        self.running = False
        self._server_socket = None
        self._client_threads = []
        self.data_callback = data_callback

    def start(self) -> None:
        self.running = True
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind(('', self.port))
            self._server_socket.listen()
            print(f"[SERVER] Listening on port {self.port}")

            while self.running:
                try:
                    self._server_socket.settimeout(1.0)
                    client_socket, client_address = self._server_socket.accept()
                    print(f"[SERVER] Accepted connection from {client_address}")

                    self._client_threads = [t for t in self._client_threads if t.is_alive()]
                    thread = threading.Thread(target=self._handle_client, args=(client_socket, client_address),
                                              daemon=True)
                    self._client_threads.append(thread)
                    thread.start()
                except socket.timeout:
                    continue
                except OSError as e:
                    if self.running:
                        print(f"[SERVER] Error accepting connection or socket error: {e}", file=sys.stderr)
                    break
                except Exception as e:
                    if self.running:
                        print(f"[SERVER] Unexpected error accepting client: {e}", file=sys.stderr)
                    continue
        except OSError as e:
            print(f"[SERVER_SETUP] CRITICAL: Could not bind to port {self.port}. Error: {e}", file=sys.stderr)
            self.running = False
            if self.data_callback:
                self.data_callback({"type": "server_error", "message": f"Could not bind to port {self.port}: {e}"})
            return
        finally:
            if self._server_socket:
                try:
                    self._server_socket.close()
                    print("[SERVER] Server socket closed.")
                except Exception as e:
                    print(f"[SERVER] Error closing server socket: {e}", file=sys.stderr)

    def stop(self):
        print("[SERVER] Stop signal received. Shutting down...")
        self.running = False


        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception as e:
                print(f"[SERVER] Error closing server socket during stop: {e}", file=sys.stderr)

        print("[SERVER] Waiting for client threads to finish...")
        for thread in self._client_threads:
            if thread.is_alive():
                try:
                    thread.join(timeout=1.0)
                    if thread.is_alive():
                        print(f"[SERVER] Thread {thread.name} unresponsive after join timeout.", file=sys.stderr)
                except Exception as e:
                    print(f"[SERVER] Error joining thread {thread.name}: {e}", file=sys.stderr)
        self._client_threads = []
        print("[SERVER] All client threads processed.")

    def _handle_client(self, client_socket, client_address):
        print(f"[SERVER] Client {client_address} connected on thread {threading.current_thread().name}")
        client_socket.settimeout(20.0)

        with client_socket:
            remaining_buffer = b''
            while self.running:
                try:
                    # 1. Odbierz dane od klienta
                    chunk = client_socket.recv(1024)
                    if not chunk:
                        print(f"[SERVER] Client {client_address} disconnected (EOF).")
                        break

                    current_data = remaining_buffer + chunk

                    while b'\n' in current_data and self.running:
                        line_end = current_data.find(b'\n')
                        complete_message = current_data[:line_end]
                        current_data = current_data[line_end + 1:]

                        if not complete_message.strip():
                            continue

                        # 2. Przetwórz wiadomość
                        try:
                            msg_str = complete_message.decode('utf-8')
                            decoded_data = json.loads(msg_str)
                            print(f"[SERVER] Received from {client_address}: {decoded_data}")

                            if self.data_callback:
                                try:
                                    self.data_callback({"type": "sensor_data", "payload": decoded_data})
                                except Exception as cb_ex:
                                    print(f"[SERVER] Error in data_callback: {cb_ex}", file=sys.stderr)

                            client_socket.sendall(b"ACK\n")

                        except json.JSONDecodeError as e_json:
                            print(f"[SERVER] JSON Decode Error from {client_address}: {e_json}. Msg: '{msg_str[:100]}...'", file=sys.stderr)
                            client_socket.sendall(b"NACK_JSON_ERROR\n")
                            if self.data_callback:
                                self.data_callback({"type": "decode_error", "message": f"JSON Decode Error from {client_address}. Msg: '{msg_str[:100]}...'"})
                        except socket.error as se_ack:
                            print(f"[SERVER] Socket error sending ACK/NACK to {client_address}: {se_ack}", file=sys.stderr)
                            self.running = False
                            break
                        except Exception as e_proc:
                            print(f"[SERVER] Error processing message/responding to {client_address}: {e_proc}", file=sys.stderr)
                            try:
                                client_socket.sendall(b"NACK_SERVER_ERROR\n")
                            except socket.error:
                                self.running = False;
                                break

                    if not self.running:
                        break
                    remaining_buffer = current_data

                except socket.timeout:
                    print( f"[SERVER] Client {client_address} timed out (inactive for {client_socket.gettimeout()}s). Closing connection.", file=sys.stderr)
                    break
                except ConnectionResetError:
                    print(f"[SERVER] Connection reset by {client_address}.", file=sys.stderr)
                    break
                except socket.error as e_sock:
                    print(f"[SERVER] Socket error with {client_address}: {e_sock}", file=sys.stderr)
                    break
                except Exception as e_critical:
                    print(f"[SERVER] Unexpected critical error handling client {client_address}: {e_critical}", file=sys.stderr)
                    break


            print(f"[SERVER] Finished handling client {client_address}. Thread {threading.current_thread().name} exiting.")



if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from network.config import load_config
    except ImportError as e:
        print(f"[SERVER_SETUP] CRITICAL: Import error 'load_config': {e}", file=sys.stderr)
        sys.exit(1)

    config_file_path = os.path.join(project_root, "config.yaml")
    server_port = 9999  # Domyślny port

    if not os.path.exists(config_file_path):
        print(f"[SERVER_SETUP] WARNING: Config '{config_file_path}' not found. Using default port {server_port}.",
              file=sys.stderr)
    else:
        try:
            config_data = load_config(config_file_path)
            if config_data and "network" in config_data and "port" in config_data["network"]:
                server_port = int(config_data["network"]["port"])  # Upewnij się, że port jest int
            else:
                print(
                    f"[SERVER_SETUP] WARNING: 'network' key or 'port' not in '{config_file_path}' or empty. Using default port {server_port}.",
                    file=sys.stderr)
        except Exception as e:
            print(
                f"[SERVER_SETUP] WARNING: Error loading config '{config_file_path}': {e}. Using default port {server_port}.",
                file=sys.stderr)

    server = NetworkServer(port=server_port)
    server_thread = None

    try:
        print(f"[SERVER_SETUP] Starting server on port {server_port}...")
        # Uruchomienie serwera w osobnym wątku, aby główny wątek mógł obsłużyć KeyboardInterrupt
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()

        # Pętla w głównym wątku, aby utrzymać program działający i móc przechwycić Ctrl+C
        while server.running and server_thread.is_alive():
            pass

    except KeyboardInterrupt:
        print("\n[SERVER_SETUP] KeyboardInterrupt received by main thread. Shutting down server...", file=sys.stderr)
    except Exception as e:
        print(f"[SERVER_SETUP] CRITICAL error in main execution block: {e}", file=sys.stderr)
    finally:
        print("[SERVER_SETUP] Main thread initiating server stop...")
        if server.running:
            server.stop()

        if server_thread and server_thread.is_alive():
            print("[SERVER_SETUP] Waiting for server thread to complete...")
            server_thread.join(timeout=5.0)
            if server_thread.is_alive():
                print("[SERVER_SETUP] Server thread did not complete in time.", file=sys.stderr)

        print("[SERVER_SETUP] Server shutdown process complete from main thread.")
