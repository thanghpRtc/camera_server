from lib.client_request import Camera_data_request
from hikvisionapi import Client
import time
import logging
from utils import func
from abc import ABC, abstractmethod
import subprocess
from lib.customAMQP import AMQP

logger = func.get_logger(__name__)




class CheckConnectReponse_method(ABC):
    @abstractmethod
    def Check_response(self, IP: str, port: 8000) ->bool:
        pass

class CheckConnect_Response_ping(CheckConnectReponse_method):
    @abstractmethod
    def Check_response(self, IP: str, port: 8000)-> bool:
        ping_result = subprocess.run(["ping", "-c", "4", IP], capture_output=True, text=True)
        if ping_result.returncode == 0:
            return True
        else:
            return False
        
class CheckConnect_Response_API(CheckConnectReponse_method):
    @abstractmethod
    def Check_response(self, IP: str, username: str, password:str) -> bool:
        client = Client("http://" +IP, username, password)
        try:
            response = client.System.deviceInfo(method='get')
            return True
        except:
            return False



class Update_camera_status():
    def __init__(self, checking_interval = 5, server_IP = "192.168.5.189", server_port = 8500):
        self.server_client = Camera_data_request(server_IP = server_IP, server_port = server_port)
        self.all_cameras = self.server_client.Get_camera_of_server(server_id = 0)
        self.checking_interval = checking_interval

    def run_checking(self, check_method: CheckConnectReponse_method):

        while(1):

            for camera_data in self.all_cameras:
                #print("Ip, username, password: %s, %s, %s" , camera_data["ipaddress"], camera_data["username"], camera_data["password"])
                try:
                    state = check_method.Check_response(camera_data)
                    if state == True:
                        self.server_client.Update_camera_status(camera_data["id"], camera_status = True)
                    else:
                        self.server_client.Update_camera_status(camera_data["id"], camera_status = False)
                        logger.error("Camera  is disconnected : {}".format(camera_data["id"]))

                except:
                    logger.error("Server is disconnected : {}".format(camera_data["id"]))
                   
            time.sleep(self.checking_interval)

    def Check_disconnect_camera(self, check_method: CheckConnectReponse_method):
        list_disconnect_camera = []
        for camera_data in self.all_cameras:
            try:
                state = check_method.Check_response(camera_data)
                if state == False:
                    list_disconnect_camera.append(camera_data["id"])
            except:
                    logger.error("Server is disconnected : {}".format(camera_data["id"]))
        return list_disconnect_camera



if __name__ == "__main__":

    check_camera = Update_camera_status()
    
    check_camera.run_checking()

