import unittest
from network.client import NetworkClient

class TestNetworkClient(unittest.TestCase):
    def test_initialization(self):
        client = NetworkClient("127.0.0.1", 8080)
        self.assertEqual(client.host, "127.0.0.1")
        self.assertEqual(client.port, 8080)