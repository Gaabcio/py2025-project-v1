import socket
import json
import logging

class NetworkClient:
    def __init__(self, host: str, port: int, timeout: float = 5.0, retries: int = 3):
        """Inicjalizuje klienta sieciowego."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.socket = None
        self.logger = logging.getLogger("NetworkClient")

    def connect(self) -> None:
        """Nawiazuje połączenie z serwerem."""
        try:
            self.socket = socket.create_connection((self.host, self.port), self.timeout)
            self.logger.info("Połączono z serwerem na %s:%d", self.host, self.port)
        except Exception as e:
            self.logger.error("Błąd podczas łączenia z serwerem: %s", e)
            raise

    def send(self, data: dict) -> bool:
        """Wysyła dane i czeka na potwierdzenie zwrotne."""
        if not self.socket:
            raise ConnectionError("Brak połączenia z serwerem.")
        
        for attempt in range(self.retries):
            try:
                serialized_data = self._serialize(data)
                self.socket.sendall(serialized_data)
                self.logger.info("Wysłano dane: %s", data)

                # Czekanie na potwierdzenie
                ack = self.socket.recv(1024).decode('utf-8').strip()
                if ack == "ACK":
                    self.logger.info("Otrzymano potwierdzenie ACK.")
                    return True
            except Exception as e:
                self.logger.error("Błąd podczas wysyłania danych: %s", e)
        
        self.logger.error("Nie udało się wysłać danych po %d próbach.", self.retries)
        return False

    def close(self) -> None:
        """Zamyka połączenie."""
        if self.socket:
            self.socket.close()
            self.logger.info("Zamknięto połączenie z serwerem.")

    def _serialize(self, data: dict) -> bytes:
        """Serializuje dane do formatu JSON."""
        return (json.dumps(data) + "\n").encode('utf-8')

    def _deserialize(self, raw: bytes) -> dict:
        """Deserializuje dane JSON."""
        return json.loads(raw.decode('utf-8'))