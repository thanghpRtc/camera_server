import subprocess
import logging
import logging.config

def Connected_to_network(ip_address):
    result = subprocess.run(['ping', '-c', '1', ip_address], stdout = subprocess.PIPE)
    return result.returncode == 0

def get_logger(name):
    logging.config.fileConfig("./log/log_config.conf")
    logger = logging.getLogger(name)
    return logger


