import socket
import time
from lib.UploaderQueues import UploaderQueues
import threading

class EmbeddedCollector:
    def __init__(self, uploader_queues: UploaderQueues):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('0.0.0.0', 12345))
        self.uploader_queues = uploader_queues
        self._stop_event = threading.Event()
    
    def stop(self):
        self._stop_event.set() 

    def listen(self):
        self._stop_event.clear()
        while not self._stop_event.is_set():
            # client_socket, address = server.accept()
            # data = client_socket.recv(1024)
            # print(f"Received: {data.decode()}")
            # client_socket.close()
            time.sleep(10)