from flask import Flask, g, request, jsonify
from lib.UploaderQueues import UploaderQueues
from lib.EmbeddedCollector import EmbeddedCollector
from lib.LaptopCollector import LaptopCollector
from lib.Logger import Logger
import threading

app = Flask(__name__)

# Global references for the collectors and their threads
embedded_collector = None
embeddedThread = None
laptop_collector = None
laptopThread = None

with app.app_context():
    # Initialize logger and uploader queues
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

    # Start periodic sending of data to server
    queueThread = threading.Thread(target=g.uploader_queues.send_periodic_request)
    queueThread.daemon = True
    queueThread.start()

# Endpoint to start / stop the collecting of data from an aggregators device
@app.route('/manage_collection', methods=['POST'])
def manage_collection():
    global embedded_collector, embeddedThread, laptop_collector, laptopThread

    # get instruction data from request
    data = request.get_json()
    instruction = data.get("instruction")
    device_name = data.get("device_name")

    if not instruction or not device_name:
        return jsonify({"message": "instruction and device_name are required"}) , 400

    try:
        if instruction == "STOP":
            # check device name and stop the respective collector
            if device_name == "esp-32" and embeddedThread and embeddedThread.is_alive():
                # stop the collector and join the thread. If you do not stop the collector the thread will not stop
                embedded_collector.stop()
                embeddedThread.join()
                logger.info("Embedded collector stopped")
                return jsonify({"message": "Embedded collector stopped successfully"}), 200
            elif device_name == "johns-laptop" and laptopThread and laptopThread.is_alive():
                laptop_collector.stop()  # Signal the thread to stop
                laptopThread.join()  # Wait for the thread to finish
                logger.info("Laptop collector stopped")
                return jsonify({"message": "Embedded collector stopped successfully"}), 200
            else:
                return jsonify({"message": f"Error starting collector {device_name}"}), 500
        elif instruction == "START":
            # check device name and start the respective collector
            if device_name =="esp-32" and not embeddedThread or not embeddedThread.is_alive():
                # Start a new EmbeddedCollector and its thread
                embeddedThread = threading.Thread(target=embedded_collector.listen)
                embeddedThread.daemon = True
                embeddedThread.start()
                logger.info("Embedded collector started")
                return jsonify({"message": "Embedded collector started successfully"}), 200
            elif device_name == "johns-laptop" and not laptopThread or not laptopThread.is_alive():
                laptopThread = threading.Thread(target=laptop_collector.get_os_metrics)
                laptopThread.daemon = True
                laptopThread.start()
                logger.info("Laptop collector started")
                return jsonify({"message": "Laptop collector started successfully"}), 200
            else:
                return jsonify({"message": f"Error starting collector {device_name}"}), 500
        else:
            return jsonify({"message": "invalid instruction"}), 400
    except Exception as e:
        logger.error(f"Error {instruction}ing {device_name} collector: {str(e)}")
        return jsonify({"message": "error executing instruction"}), 500

if __name__ == '__main__':
    app.run()

