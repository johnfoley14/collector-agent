import psutil
from lib.models.DeviceData import DeviceData
from lib.UploaderQueues import UploaderQueues
from datetime import datetime
import time

class LaptopCollector:
    def __init__(self, uploader_queues: UploaderQueues):
        self.uploader_queues = uploader_queues

    def get_os_metrics(self, interval: int = 1):
        # Get RAM usage every second
        while True:
            ram_usage = psutil.virtual_memory().percent
            io_counters_start = psutil.disk_io_counters()
            time.sleep(interval)
            io_counters_end = psutil.disk_io_counters()

            # calculate read and write rates
            read_rate = (io_counters_end.read_bytes - io_counters_start.read_bytes) / interval
            write_rate = (io_counters_end.write_bytes - io_counters_start.write_bytes) / interval
            self.uploader_queues.add_to_laptop_queue(DeviceData(datetime.now().isoformat(), {'RAM Use': ram_usage, 'Read Rate': read_rate, 'Write Rate': write_rate}))
            
