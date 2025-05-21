import socket
import json
import logging

class NetworkServer:
    def __init__(self, port: int):
        """Inicjalizuje serwer na wskazanym porcie."""
        self.port = port
        self.logger = logging.getLogger("NetworkServer")

    def start(self) -> None:
        """Uruchamia nasłuchiwanie połączeń i obsługę klientów."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(('0.0.0.0', self.port))
            server_socket.listen()
            self.logger.info("Serwer nasłuchuje na porcie %d", self.port)

            while True:
                client_socket, addr = server_socket.accept()
                self.logger.info("Połączono z klientem: %s", addr)
                with client_socket:
                    self._handle_client(client_socket)

    def _handle_client(self, client_socket) -> None:
        """Odbiera dane, wysyła ACK i wypisuje je na konsolę."""
        try:
            raw_data = client_socket.recv(1024)
            data = self._deserialize(raw_data)
            print("Otrzymano dane:", data)
            
            # Wysłanie potwierdzenia ACK
            client_socket.sendall("ACK\n".encode('utf-8'))
        except json.JSONDecodeError as e:
            self.logger.error("Błąd parsowania JSON: %s", e)
        except Exception as e:
            self.logger.error("Błąd podczas obsługi klienta: %s", e)

    def _deserialize(self, raw: bytes) -> dict:
        """Deserializuje dane JSON."""
        return json.loads(raw.decode('utf-8'))