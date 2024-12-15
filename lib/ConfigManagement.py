import json

class ConfigManagement:
    def __init__(self):
        self.config = None
        self.logger_config = None
        self.devices = None

    def load_config(self):
        with open('./config.json') as f:
            self.config = json.load(f)
            self.logger_config = self.config.get("logger")
            self.devices = self.config.get("devices")
    
    def get_config(self):
        return self.config

    def get_logger_config(self):
        return self.logger_config
    
    def get_devices(self):
        return self.devices
    
    def get_key(self, key):
        return self.config[key]
