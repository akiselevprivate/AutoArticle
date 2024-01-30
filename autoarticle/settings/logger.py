import logging
from datetime import datetime
import os


# Define a format for the log
try:
    os.mkdir("logs")
except:
    pass
log_file_name = f"logs/logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

format_log = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    filename=log_file_name,  # Specify the file to save logs to
    level=logging.DEBUG,  # Set the logging level to include DEBUG messages
    format=format_log,
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter and add it to the handler
console_formatter = logging.Formatter(format_log)
console_handler.setFormatter(console_formatter)

# Add the handler to the root logger
logging.getLogger("").addHandler(console_handler)


# # Add the handlers to the logger
logger = logging.getLogger(__name__)
