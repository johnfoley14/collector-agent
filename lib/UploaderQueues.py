from queue import Queue
from lib.models.DeviceData import DeviceData
from lib.ConfigManagement import ConfigManagement
from lib.Logger import Logger
import requests
import time
import threading

class UploaderQueues:
    def __init__(self, logger: Logger):
        self.embedded_data_queue = Queue()
        self.laptop_data_queue = Queue()
        self.logger = logger
        self.config_manager = ConfigManagement()
        self.config_manager.load_config()

    def set_collector_threads(self, thread_resources):
        self.embedded_collector = thread_resources.get("embedded_collector")
        self.embeddedThread = thread_resources.get("embeddedThread")
        self.laptop_collector = thread_resources.get("laptop_collector")
        self.laptopThread = thread_resources.get("laptopThread")

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
    
    def send_periodic_request(self):
        while True:
            # Sleep for 10 seconds (avoiding busy waiting to save CPU cycles)
            time.sleep(10)
                
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

            # We now need to send requests even if no data so the aggregator can know if collector has restarted
            # # If no data to send to not send request
            # if laptop_count == 0 and embedded_count == 0:
            #     continue

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
                # response = requests.post('https://johnfoley14.pythonanywhere.com/post_metrics', json=payload)
                response = requests.post('http://localhost:5001/post_metrics', json=payload)
                if response.status_code == 200:
                    for device in self.config_manager.get_devices():
                        self.manage_collection(device, response.json().get("message").get(device))
                    self.logger.info(f"Data sent to server: {response.status_code, response.text}")
                else:
                    self.logger.error(f"Error sending data to server: {response.status_code, response.text}")
            except requests.RequestException as e:
                self.logger.error(f"Error sending data to server: {e}")

    # turn off/on data collection as needed
    def manage_collection(self, device_name, instruction):
        try:
            if instruction == "STOP":
                if device_name == "esp-32" and self.embeddedThread and self.embeddedThread.is_alive():
                    # stop signals the thread to stop collecting data and exit the function
                    self.embedded_collector.stop()
                    self.embeddedThread.join()
                    self.logger.info(f"Embedded collector stopped. Thread count: {len(threading.enumerate())}")
                    return True
                elif device_name == "johns-laptop" and self.laptopThread and self.laptopThread.is_alive():
                    self.laptop_collector.stop()
                    self.laptopThread.join()
                    self.logger.info(f"Laptop collector stopped. Thread count: {len(threading.enumerate())}")
                    return True
            elif instruction == "START":
                if device_name == "esp-32" and (not self.embeddedThread or not self.embeddedThread.is_alive()):
                    self.embeddedThread = threading.Thread(target=self.embedded_collector.listen)
                    self.embeddedThread.daemon = True
                    self.embeddedThread.start()
                    self.logger.info(f"Embedded collector started. Thread count: {len(threading.enumerate())}")
                    return True
                elif device_name == "johns-laptop" and (not self.laptopThread or not self.laptopThread.is_alive()):
                    self.laptopThread = threading.Thread(target=self.laptop_collector.get_os_metrics)
                    self.laptopThread.daemon = True
                    self.laptopThread.start()
                    self.logger.info(f"Laptop collector started. Thread count: {len(threading.enumerate())}")
                    return True
            else:
                self.logger.error("Invalid instruction")
                return False
        except Exception as e:
            self.logger.error(f"Error {instruction}ing {device_name} collector: {str(e)}")
            return False
    