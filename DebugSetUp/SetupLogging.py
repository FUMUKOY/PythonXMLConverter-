import logging
import os

def setup_logging():

    log_directory = "C:\AppLogs\Python" 
    log_file_path = os.path.join(log_directory, "Python_command_line.log") 

    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename=log_file_path,
    )



