from flask import Flask, g
import threading

from lib.UploaderQueues import UploaderQueues
from lib.EmbeddedCollector import EmbeddedCollector
from lib.LaptopCollector import LaptopCollector
from lib.Logger import Logger

app = Flask(__name__)

with app.app_context():
    # Initialize logger, uploader queues and config manager
    embedded_collector = None
    embeddedThread = None
    laptop_collector = None
    laptopThread = None
    logger = Logger()
    g.uploader_queues = UploaderQueues(logger)
    
    # Start embedded collector
    def start_embedded_collector():
        global embedded_collector, embeddedThread
        embedded_collector = EmbeddedCollector(g.uploader_queues)
        embeddedThread = threading.Thread(target=embedded_collector.listen)
        embeddedThread.daemon = True
        embeddedThread.start()

    start_embedded_collector()  # Start the embedded thread when the app starts

    # Start OS metrics collector
    def start_laptop_collector():
        global laptop_collector, laptopThread
        laptop_collector = LaptopCollector(g.uploader_queues)
        laptopThread = threading.Thread(target=laptop_collector.get_os_metrics)
        laptopThread.daemon = True
        laptopThread.start()

    start_laptop_collector()  # Start the laptop thread when the app starts

    # reference to collector threads so uploader queue can turn them off
    thread_resources = {
        "embedded_collector" : embedded_collector,
        "embeddedThread" : embeddedThread,
        "laptop_collector" : laptop_collector,
        "laptopThread" : laptopThread
    }

    UploaderQueues.set_collector_threads(g.uploader_queues, thread_resources)

    # Start periodic sending of data to server
    queueThread = threading.Thread(target=g.uploader_queues.send_periodic_request)
    queueThread.daemon = True
    queueThread.start()


if __name__ == '__main__':
    app.run()

