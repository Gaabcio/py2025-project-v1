import socket
import json
import time
from datetime import datetime # <<< DODANO IMPORT

class NetworkClient:
    """
    Klient TCP do wysyłania danych w formacie JSON z obsługą powtórzeń, potwierdzenia i logowania zdarzeń.
    """
    def __init__(self, host, port, timeout=5.0, retries=3, logger=None):
        """
        Inicjalizuje klienta sieciowego.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.sock = None
        self.logger = logger

    def connect(self):
        """
        Nawiązuje połączenie z serwerem.
        Rzuca wyjątek w przypadku niepowodzenia.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout) # Ustawienie timeoutu dla operacji gniazda
        try:
            self.sock.connect((self.host, self.port))
            if self.logger:
                # Przekazuj datetime.now() zamiast sformatowanego stringa
                self.logger.log_reading("network", datetime.now(), 1, "connect_success")
            print(f"Successfully connected to {self.host}:{self.port}")
        except socket.timeout:
            if self.logger:
                self.logger.log_reading("network", datetime.now(), 0, "connect_timeout")
            # Rzuć wyjątek dalej, aby main.py mógł go obsłużyć i np. zakończyć program
            raise TimeoutError(f"Connection to {self.host}:{self.port} timed out after {self.timeout}s")
        except ConnectionRefusedError:
            if self.logger:
                self.logger.log_reading("network", datetime.now(), 0, "connect_refused")
            raise ConnectionRefusedError(f"Connection to {self.host}:{self.port} was refused.")
        except Exception as e:
            if self.logger:
                self.logger.log_reading("network", datetime.now(), 0, f"connect_error: {type(e).__name__}")
            raise Exception(f"Failed to connect to {self.host}:{self.port}: {e}")


    def send(self, data: dict) -> bool:
        """
        Wysyła dane (dict) jako JSON i czeka na ACK. Zwraca True/False.
        """
        if not self.sock:
            if self.logger:
                self.logger.log_reading("network", datetime.now(), 0, "send_fail_no_socket")
            print("Cannot send data: socket is not available.")
            return False

        msg = self._serialize(data)
        for i in range(self.retries):
            try:
                # print(f"Attempting to send (try {i+1}/{self.retries}): {data}") # Debug log
                self.sock.sendall(msg + b'\n')
                ack = self.sock.recv(1024) # Ta operacja również podlega timeoutowi gniazda
                if b"ACK" in ack:
                    if self.logger:
                        self.logger.log_reading("network", datetime.now(), 1, "send_ack_received")
                    return True
                else:
                    # Otrzymano coś innego niż ACK (np. NACK od serwera)
                    decoded_ack = ack.decode(errors='ignore').strip()
                    if self.logger:
                        self.logger.log_reading("network", datetime.now(), 0, f"send_nack_or_unexpected_response: {decoded_ack}")
                    print(f"Received unexpected response from server: {decoded_ack}")
                    # Jeśli serwer wysyła konkretny NACK, możemy nie chcieć ponawiać
                    # Na razie ponawiamy, chyba że to ostatnia próba
                    if i < self.retries - 1:
                        time.sleep(0.5) # Czekaj przed ponowieniem
                    continue # Przejdź do następnej próby

            except socket.timeout:
                if self.logger:
                    self.logger.log_reading("network", datetime.now(), 0, f"send_timeout_attempt_{i+1}")
                print(f"Send attempt {i+1}/{self.retries} timed out.")
                if i == self.retries - 1: # Ostatnia próba
                    print("Send failed after all retries due to timeout.")
                    return False # Ostateczne niepowodzenie po timeoutach
                time.sleep(0.5) # Czekaj przed ponowieniem
            except socket.error as e: # Np. ConnectionResetError, BrokenPipeError
                if self.logger:
                    self.logger.log_reading("network", datetime.now(), 0, f"send_socket_error_attempt_{i+1}: {type(e).__name__}")
                print(f"Socket error during send attempt {i+1}/{self.retries}: {e}")
                # W przypadku błędu gniazda, dalsze próby na tym samym gnieździe mogą być bezcelowe.
                # Można by tu zamknąć gniazdo i spróbować połączyć się ponownie, lub od razu zwrócić False.
                self.close() # Zamknij gniazdo, bo jest prawdopodobnie w złym stanie
                return False # Ostateczne niepowodzenie z powodu błędu gniazda
            except Exception as e: # Inne nieoczekiwane błędy
                if self.logger:
                    self.logger.log_reading("network", datetime.now(), 0, f"send_generic_error_attempt_{i+1}: {type(e).__name__}")
                print(f"Generic error during send attempt {i+1}/{self.retries}: {e}")
                if i == self.retries - 1:
                    return False
                time.sleep(0.5)

        # Jeśli pętla zakończyła się bez zwrócenia True (np. wszystkie próby NACK)
        if self.logger:
            self.logger.log_reading("network", datetime.now(), 0, "send_fail_after_retries_no_ack")
        print("Send failed after all retries (no ACK or unexpected response).")
        return False

    def close(self):
        """
        Zamyka połączenie.
        """
        if self.sock:
            try:
                self.sock.close()
                if self.logger:
                    self.logger.log_reading("network", datetime.now(), 1, "close_success")
                print("Network client socket closed.")
            except Exception as e:
                if self.logger:
                    self.logger.log_reading("network", datetime.now(), 0, f"close_error: {type(e).__name__}")
                print(f"Error closing socket: {e}")
            finally:
                self.sock = None # Upewnij się, że gniazdo jest None po zamknięciu

    def _serialize(self, data: dict) -> bytes:
        return json.dumps(data).encode('utf-8')

    def _deserialize(self, raw: bytes) -> dict: # Nie jest używane w kliencie
        return json.loads(raw.decode('utf-8'))
