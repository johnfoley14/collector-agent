from flask import Flask, g
from lib.UploaderQueues import UploaderQueues
from lib.EmbeddedCollector import EmbeddedCollector
from lib.LaptopCollector import LaptopCollector
from lib.Logger import Logger
import threading

app = Flask(__name__)

with app.app_context():
    logger = Logger()
    g.uploader_queues = UploaderQueues(logger)

    # Start embedded collector
    embedded_collector = EmbeddedCollector(g.uploader_queues)
    embeddedThread = threading.Thread(target=embedded_collector.listen)
    embeddedThread.daemon = True
    embeddedThread.start()

    # Start OS metrics collector
    laptop_collector = LaptopCollector(g.uploader_queues)
    laptopThread = threading.Thread(target=laptop_collector.get_os_metrics)
    laptopThread.daemon = True
    laptopThread.start()

    # Start periodic sending of data to server
    queueThread = threading.Thread(target=g.uploader_queues.send_periodic_request)
    queueThread.daemon = True
    queueThread.start()

if __name__ == '__main__':
    app.run()
