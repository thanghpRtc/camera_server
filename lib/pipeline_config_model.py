from pydantic import BaseModel,EmailStr,ValidationError
import json
from typing import List, Union, Dict

class Tiler_model(BaseModel):
    enable:str
    rows:str
    columns:str
    width:str
    height:str
    gpu_id:str
    nvbuf_memory_type: str


class Source_model(BaseModel):
    enable:str
    type:str
    gpu_id:str
    uri:str
    camera_width:str
    camera_height:str
    camera_fps_n:str
    camera_fps_d:str 
    rtsp_reconnect_interval_sec: str
    rtsp_reconnect_attempts: str

class Sources_input():
    sources_input: List[Source_model] = []

    def Add_source(self,item):
        
        self.sources_input.append(item)

class Sink_display_model(BaseModel):
    enable:str
    sync:str
    source_id:str
    gpu_id:str
    qos:str
    nvbuf_memory_type:str

class Sink_rtsp_model(BaseModel):
    enable:str
    codec:str
    enc_type:str
    sync:str
    bitrate: str
    profile:str
    rtsp_port:str
    udp_port:str
    host:str
    qos:str
    rtsp_host:str


class OSD_model(BaseModel):
    enable:str
    gpu_id:str
    border_width:str
    text_size:str
    font:str
    show_clock:str
    clock_x_offset:str
    clock_y_offset:str
    clock_text_size:str
    nvbuf_memory_type:str
    process_mode:str
    display_text:str 

class Tracker_model(BaseModel):
    file:str

class Streammux_model(BaseModel):
    gpu_id:str
    live_source:str
    buffer_pool_size: str
    batch_size:str
    batched_push_timeout:str
    width: str
    height:str
    enable_padding:str
    nvbuf_memory_type:str

class Msgbroker_model(BaseModel):
    type: str #0: default amqp, 1: thread amqp
    msgconv_file:str
    msgbroker_file:str
    lib_file:str

class Analytic_model(BaseModel):
    file:str

class Pgie(BaseModel):
    #enable:str
    file:str
    interval: str


   












