import unittest
from server.server import NetworkServer

class TestNetworkServer(unittest.TestCase):
    def test_initialization(self):
        server = NetworkServer(8080)
        self.assertEqual(server.port, 8080)