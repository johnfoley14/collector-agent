from queue import Queue
from lib.models.DeviceData import DeviceData
from lib.Logger import Logger
import requests
import time
from datetime import datetime

class UploaderQueues:
    def __init__(self, logger: Logger):
        self.embedded_data_queue = Queue()
        self.laptop_data_queue = Queue()
        self.logger = logger

    def add_to_embedded_queue(self, data: DeviceData):
        self.embedded_data_queue.put(data)

    def add_to_laptop_queue(self, data: DeviceData):
        self.laptop_data_queue.put(data)

    def get_from_embedded_queue(self)-> DeviceData:
        if not self.embedded_data_queue.empty():
            return self.embedded_data_queue.get()
        return None

    def get_from_laptop_queue(self)-> DeviceData:
        if not self.laptop_data_queue.empty():
            return self.laptop_data_queue.get()
        return None

    def is_embedded_queue_empty(self)-> bool:
        return self.embedded_data_queue.empty()

    def is_laptop_queue_empty(self)-> bool:
        return self.laptop_data_queue.empty()
    
    # Periodically send data to server
    def send_periodic_request(self):
        while True:
            # Sleep for 10 seconds (avoiding busy waiting to save CPU cycles)
            time.sleep(5)
            
            laptop_data = []
            laptop_count = 0
            while not self.is_laptop_queue_empty():
                data = self.get_from_laptop_queue()
                if data:  # Ensure data is not None
                    laptop_count += 1
                    laptop_data.append(data.__dict__)
            
            embedded_data = []
            embedded_count = 0
            while not self.is_embedded_queue_empty():
                data = self.get_from_embedded_queue()
                if data:  # Ensure data is not None
                    embedded_count += 1
                    embedded_data.append(data.__dict__)

            payload = {
                "devices": [
                    {"name": "johns-laptop", "data": laptop_data},
                    {"name": "esp-32", "data": embedded_data},
                ],
                "guid": "12347",
            }

            self.logger.info(f"Sending data to server: laptop-entries: {laptop_count}, embedded-entries: {embedded_count}")
            # Send data to the server
            try:
                response = requests.post('http://localhost:5001/post_metrics', json=payload)
                if response.status_code == 200:
                    self.logger.info(f"Response from server: {response.status_code, response.text}")
                else:
                    self.logger.error(f"Error sending data to server: {response.status_code, response.text}")
            except requests.RequestException as e:
                self.logger.error(f"Error sending data to server: {e}")