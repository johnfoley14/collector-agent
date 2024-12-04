import datetime
import sys
import pickle
import json

class Logger:
    def __init__(self, log_file='./logs/app.log'):
        self.log_file = log_file
        
        with open('./config.json') as f:
            self.config = json.load(f)
            self.logger_config = self.config.get("logger")

        # Note that the IDE automatically knows to color words such as INFO, DEBUG etc
        self.log_levels = self.logger_config['levels']
        self.current_level = self.log_levels['INFO']

    def set_level(self, level):
        if level in self.log_levels:
            self.current_level = self.log_levels[level]
        else:
            raise ValueError(f"Invalid log level: {level}")

    def _log(self, level, message, color=None):
        RESET = "\033[0m"
        if self.log_levels[level] >= self.current_level:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.log_file, 'ab') as file:
                log_entry_prefix = f"{timestamp} - {level} - "

                # log strings normally
                if isinstance(message, str):
                    # Write the string message as bytes
                    log_message = log_entry_prefix + message + "\n"
                    file.write(log_message.encode('utf-8'))
                # deserialize objects and log them with pickle
                else:
                    # Write the log entry prefix first
                    file.write(log_entry_prefix.encode('utf-8'))
                    # Serialize the non-string object with pickle and add a newline separator
                    pickle.dump(message, file)
                    file.write(b"\n")  # Separate each log entry with a newline
        
        sys.stdout.write(color + f"{level} - {message}\n" + RESET)

    def debug(self, message):
        self._log('DEBUG', message, "\033[34m")

    def info(self, message):
        self._log('INFO', message, "\033[32m")

    def warning(self, message):
        self._log('WARNING', message, "\033[33m")

    def error(self, message):
        self._log('ERROR', message, "\033[31m")

    def critical(self, message):
        self._log('CRITICAL', message, "\033[31m")
