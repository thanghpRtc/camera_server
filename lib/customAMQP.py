import logging
import pika
import threading
from lib.ParseFile import ParseTXTConfig
import sys

class AMQP():
    def __init__(self, config_file):
        parse_file = ParseTXTConfig(config_file)
        config_data = parse_file.ReadData()['message-broker']
        self.username = config_data['username']
        self.password = config_data['password']
        self.exchange = config_data['exchange']
        self.period = int(config_data['period'])
        self.host = config_data['hostname']
        print("host : {}".format(self.host))
        self.number_update_camera = int(config_data['number_camera_data'])
        self.port = config_data['port']
        self.topic = config_data['topic']
        credentials = pika.PlainCredentials(username = self.username, password = self.password)
        connect_param = pika.ConnectionParameters(
            host= self.host, port = self.port,
            credentials=credentials
        )
        try:
            self.connection = pika.BlockingConnection(connect_param)
            logging.info("Connect success")
            print("success : {}".format(self.host))
        except:
            logging.error("Cannot connect to AMQP server")
            sys.exit()

        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange = self.exchange, exchange_type='topic')

    def Close(self):
        self.connection.close()

    def Send_data(self, data):
        self.channel.basic_publish(
            exchange=self.exchange, routing_key=self.topic, body=str(data))




#sender = AMQP_sender("/home/rtc/Documents/deepstream_custom/config_file/msgBroker_config/cfg_amqp.txt")


