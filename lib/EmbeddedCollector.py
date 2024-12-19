from lib.UploaderQueues import UploaderQueues
from lib.models.DeviceData import DeviceData

import socket
import threading
import select
import struct
from datetime import datetime
import requests

class EmbeddedCollector:
    def __init__(self, uploader_queues: 'UploaderQueues'):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 0.0.0.0 allows connections from any IP address, 12345 is the port number it listens at
        # app runs on port 500 but listens at 12345, by this port binding mechanism
        self.server.bind(('0.0.0.0', 12345))
        self.uploader_queues = uploader_queues
        self._stop_event = threading.Event()
        self.conn = None
        self.addr = None
        self.url = f"http://192.168.18.30/message_embedded"

    def stop(self):

        self.uploader_queues.logger.info("Closing the connection to the embedded device")
        
        data = {"message": 0}
        
        requests.post(self.url, json=data)
        
        # Set the stop event to signal the thread to stop
        self._stop_event.set()

    def listen(self):
        # Reset the stop event and re-open the socket
        self._stop_event.clear()
        self.server.listen()
        self.uploader_queues.logger.info(f"Listening at {self.server.getsockname()}")
        data = {"message": 1}
        requests.post(self.url, json=data) 

        while not self._stop_event.is_set():
            try:
                # Use select to avoid blocking indefinitely on accept()
                ready_to_read, _, _ = select.select([self.server], [], [], 1)  # 1 second timeout
                if ready_to_read:
                    self.conn, self.addr = self.server.accept()
                    self.uploader_queues.logger.info(f"Connected to {self.addr}")
                    while not self._stop_event.is_set():
                        data = self.conn.recv(1024)
                        if not data:
                            break
                        self.parse_byte_array_to_snapshots(data)
            except Exception as e:
                self.uploader_queues.logger.info(f"Connected to {self.addr}")                
            finally:
                # Close the connection after data exchange or if an error occurs
                if self.conn:
                    self.conn.close()

    def parse_byte_array_to_snapshots(self, byte_array):
        # Parse the initial time since boot (8 bytes)
        initial_boot_time, = struct.unpack_from(">Q", byte_array, 0)

        # Current time in microseconds
        current_time_us = int(datetime.utcnow().timestamp() * 1_000_000)

        # Offset after the initial 8 bytes for boot time
        byte_offset = 8

        # Iterate through the remaining bytes and parse snapshots
        snapshot_size = 17  # button_state (1) + free_heap_size (4) + motion_reading (4) + timestamp (8)
        while byte_offset + snapshot_size <= len(byte_array):
            # Parse fields of a snapshot
            button_state = byte_array[byte_offset] != 0
            free_heap_size = struct.unpack_from(">I", byte_array, byte_offset + 1)[0]
            motion_reading = struct.unpack_from(">I", byte_array, byte_offset + 5)[0]
            snapshot_timestamp = struct.unpack_from(">Q", byte_array, byte_offset + 9)[0]

            # Adjust the timestamp based on the current time
            adjusted_timestamp = current_time_us + snapshot_timestamp - initial_boot_time

            # Add the snapshot to the list
            device = DeviceData(datetime.utcfromtimestamp(adjusted_timestamp / 1_000_000).isoformat(), {'Button State': button_state, 'Free Heap Size': free_heap_size, 'Motion Reading': motion_reading})
            self.uploader_queues.add_to_embedded_queue(device)

            # print("Motion readings: ", device.metrics['Motion Reading'])

            # Advance the offset
            byte_offset += snapshot_size
