from lib.pipeline_config_model import *
import pydantic
import pytest
import sys, os
import json
from lib.ParseFile import ParseTXTConfig
from typing import Callable, Union, Dict, List


class Pipline_Config():
    
    def __init__(self, config_file: str):
        parseFile = ParseTXTConfig(config_file)
        self.file_data = parseFile.ReadData()
        # self.config_type_creation = {

        #     "tiled": Tiler_model,
        #     "sink_display": Sink_display_model,
        #     "sink_rtsp": Sink_rtsp_model,
        #     "osd": OSD_model,
        #     "streammux": Streammux_model,
        #     "msgbroker": Msgbroker_model

        # }
        self.sink_rtsp = None
        self.tiler = None
        self.sink_display = None
        self.streammux = None
        self.osd = None
        self.tracker = None
        self.pgie = None
        self.analytic = None
        self.tracker = None
        self.msgbroker = None


        self.sources = Sources_input()
         
    def load(self):
        #print(self.file_data)
       
        for key_element, element in self.file_data.items():
         
            if key_element.split("_")[0] == "source":
                item = Source_model(**element)
                self.sources.Add_source(item)

            elif key_element.split("_")[0] == "tiled":
                self.tiler = Tiler_model(**element)

            elif key_element.split("_")[0] == "sink-display":
          
                self.sink_display = Sink_display_model(**element)

            elif key_element.split("_")[0] == "sink-rtsp":
                self.sink_rtsp = Sink_rtsp_model(**element)

            elif key_element.split("_")[0] == "streammux":
                self.streammux = Streammux_model(**element)

            elif key_element.split("_")[0] == "osd":
                self.osd = OSD_model(**element)

            elif key_element.split("_")[0] == "msgbroker":
                self.msgbroker = Msgbroker_model(**element)

            elif key_element.split("_")[0] == "analytic":
                self.analytic = Analytic_model(**element)

            elif key_element.split("_")[0] == "pgie":
                self.pgie = Pgie(**element)
                print("file: {}".format(self.pgie.file))

            elif key_element.split("_")[0] == "tracker":
                self.tracker = Tracker_model(**element)
            

            

            # elif key_element.split("_")[0] == "pgie":
            #     self
            
        
# config = Pipline_Config("/home/rtc/Documents/deepstream_custom/config_file/init_config/pipeline_config.txt")
# config()
# print(config.msgbroker.type)

# print("ok")

            
            




    


