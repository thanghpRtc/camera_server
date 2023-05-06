
import requests
import time
import json
import logging
from typing import Dict, List, Union

logging.basicConfig(level = logging.INFO,
                    format = "%(asctime)s %(levelname)s %(message)s",
                    )

# url = "http://192.168.5.189:8500/camera_data/add_new_analytic_param/1"
# param = {
#                 "item_name": "di_vao2",
#                 "type": "line",
#                 "total": 0,
#                 "parse": "",
#                 "empty": True
#                 }
# #response = requests.post(url, json = param).json()
class RequestFail_Error(Exception):
    pass

class Client_request():
    def __init__(self, server_IP: str, server_port : int ):
        self.server_IP = server_IP
        self.server_port = server_port
        self.base_url = "http://" + server_IP + ":" + str(server_port)
    #Check if server is running
    def Check_response(self) -> bool:
        response = requests.get(self.base_url +"/docs")
        status_code = response.status_code
        if status_code == 200:
            logging.info("Test connect to server successful")
            return True
        else:
            return False
        
class Camera_data_request(Client_request):
    def __init__(self, server_IP: str, server_port: int):
        super(Camera_data_request, self).__init__(server_IP, server_port)
        self.url_frame = self.base_url + "/camera_data"

    def Get_analytic_item(self, analytic_name: str):
        url = self.url_frame + "/get_analytic_item/" + analytic_name
        response = requests.get(url)
        if response.status_code == 200:
            response_data = response.json()
            if response_data == None:
                return None
            else:
                return response_data
            
        else:
            raise RequestFail_Error("Cannot execute request")
        return None

    def Get_camera_connect(self, camera_id: int):
        url = self.url_frame + "/get_camera_connect/" + str(camera_id)
        response = requests.get(url)
        if response.status_code == 200:
            response_data = response.json()
            if response_data == None:
                return None
            else:
                return response_data

        else:
            raise RequestFail_Error("Cannot execute request")
        return None
    
    def Get_camera_of_server(self, server_id:int):
        url = self.url_frame + "/get_cameras_of_server/" + str(server_id)
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise RequestFail_Error("Cannot execute request")

    def Check_exist_analytic_item(self, analytic_name):
        data = self.Get_analytic_item(analytic_name)
        if data is None:
            return False
            
        return True

    #Add new analytics item to database
    def Post_new_analytic_item(self, camera_id: int, analytic_name:str, analytic_type:str) -> bool:
        available_type = ['line', 'roi', 'direct', 'overcrowd']
        if analytic_type in available_type:
            
            post_payload = {
                "item_name": analytic_name,
                "type": analytic_type,
                "total": 0,
                "parse": "",
                "empty": False
                
            }
            url = self.url_frame + "/add_new_analytic_param/" + str(camera_id)
           
            response = requests.post(url, json = post_payload)
            if response.status_code == 200:
                return True
            else:
                raise RequestFail_Error("Can not add new analytics item to database")
                
        else:
            raise ValueError("analytic_type value is not correct")
        return False

    #Add new camera to database
    def Post_new_camera(self,name :str, id: int, ipaddress: str, server_id:int, camera_brand = "hik", username = "admin",password = "rtc12345", port = 8000)-> bool:
        post_payload = {
            "name": name,
            "username": username, 
            "id": id,
            "camera_brand": camera_brand,
            "ipaddress": ipaddress,
            "port": port,
            "password": password,
            "status": False,
            "server_id": server_id,
            "imageTemplate": ""

        }
        url = self.url_frame + "/add_new_camera_connect/"
        response = requests.post(url, json = post_payload)
        if response.status_code == 200:
            return True
        else:
            raise RequestFail_Error("Can not add new camera")
        return False
        
    #Remove analytic item from database   
    def Delete_camera_analytic_item(self,analytic_name:str) -> bool:
        url = self.base_url + "/remove_analytic_item/" + analytic_name
        reponse = requests.delete(url)
        if reponse.status_code == 200:
            return True
        else:
            raise RequestFail_Error("Can not delete analytics item")
        return False

    def Delete_server_data(self, server_id: int) -> bool:
        url = self.base_url + "/remove_camera_server/" + str(server_id)
        response = requests.delete(url)
        if response.status_code == 200:
            return True
        else: 
            raise RequestFail_Error(f"Can not delete data of server {server_id}")
        return False

    def Update_camera_status(self, camera_id, camera_status) -> bool:
        url = self.url_frame + "/update_camera_state/" + str(camera_id)
        if camera_status == True:
            url = url + "?status=true"
        else: url = url + "?status=false"
        response = requests.put(url,)
        if response.status_code == 200:
            print(response.json())
            return True
        
        return False
    

    
            
    
#client = Client_request(server_IP = "192.168.5.189", server_port= 8500)

# # client.Check_response()
# client = Camera_data_request(server_IP = "192.168.5.189", server_port = 8500)
# status = client.Update_camera_status(1, True )
# print(status)
# # status = client.Post_new_camera("caca", id = 5, ipaddress="3243", server_id = 2)
# print(status)

    
        
        
        


