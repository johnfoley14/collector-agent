import psutil
from lib.models.DeviceData import DeviceData
from lib.UploaderQueues import UploaderQueues
from datetime import datetime
import threading

class LaptopCollector:
    def __init__(self, uploader_queues: UploaderQueues):
        self.uploader_queues = uploader_queues        
        self._stop_event = threading.Event()
    
    def stop(self):
        # Signal an event to stop the thread
        self._stop_event.set() 


    def get_os_metrics(self):
        # when a new thread is created, the stop event is cleared to collect data again
        self._stop_event.clear()
        # Get RAM usage every second
        while not self._stop_event.is_set():
            ram_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent(interval=1)

            self.uploader_queues.add_to_laptop_queue(DeviceData(datetime.now().isoformat(), {'RAM Use': ram_usage, 'CPU Use': cpu_usage}))
            
