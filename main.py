#!/usr/bin/env python3

################################################################################
# SPDX-FileCopyrightText: Copyright (c) 2020-2021 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import sys
import json

sys.path.append('../')
import gi
import configparser

gi.require_version('Gst', '1.0')
gi.require_version("GstRtspServer", "1.0")
from gi.repository import GLib, Gst, GstRtspServer
from ctypes import *
import time
import sys
import math
import platform
import threading
import socket
from optparse import OptionParser

import numpy as np
import pyds
import cv2
import os
import os.path
from os import path
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.FPS import PERF_DATA
from common.utils import long_to_uint64
from lib.ParsePipline_config import Pipline_Config
from lib.customAMQP import AMQP
from  utils import Label_load
from deepstream_pipeline_element import *
from dataFormat import TransmitFrameConfig, BasicAnalyticItem2Dict, FullAnalyticItem2Dict
from copy import deepcopy
import logging
import logging.config
import pika
import threading
import datetime
from utils import func
from check_camera_health import Update_camera_status, CheckConnect_Response_ping

date_normal = datetime.date.today()

date = datetime.datetime.now()
logger = func.get_logger(__name__)

MAX_TIME_STAMP_LEN = 32


class Pipeline():
    def __init__(self, config_pipeline: str, classes_file = "./config_file/infer_config/label/labelV5.txt"):
        logger.info("start pipeline")
        self.frame_number = 0
        self.pipeline_config = Pipline_Config(config_pipeline)
        self.pipeline_config.load()
        self.pgie_classes_str = Label_load.load_classes(classes_file)
        self.transmitFrame = TransmitFrameConfig(self.pipeline_config.analytic.file, classes_file)
        self.send_data ={}
 

    def tiler_sink_pad_buffer_probe(self, pad, info, u_data):
        
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            logger.info("Unable to get GstBuffer ")
            return
    
        # Retrieve batch metadata from the gst_buffer
        # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
        # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
        l_frame = batch_meta.frame_meta_list
        self.enable_tran = False
        
        while l_frame:
            try:
                # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
                # The casting is done by pyds.NvDsFrameMeta.cast()
                # The casting also keeps ownership of the underlying memory
                # in the C code, so the Python garbage collector will leave
                # it alone.
                frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
                #logger.info("frame num: {}".format(frame_meta.frame_num))
            except StopIteration:
                break

            self.frame_number=frame_meta.frame_num
            l_obj=frame_meta.obj_meta_list
            num_rects = frame_meta.num_obj_meta
            # obj_counter = {
            # CLASS_BOX :0

            # }
            
            #logger.info("#"*50)
            
            while l_obj:
            
                    #self.transmitFrame.ResetAllData()

                try: 
                    # Note that l_obj.data needs a cast to pyds.NvDsObjectMeta
                    # The casting is done by pyds.NvDsObjectMeta.cast()
                    obj_meta=pyds.NvDsObjectMeta.cast(l_obj.data)
                except StopIteration:
                    break
                l_user_meta = obj_meta.obj_user_meta_list
                
                
                # Extract object level meta data from NvDsAnalyticsObjInfo
                
                while l_user_meta:
                    
                    try:
                        user_meta = pyds.NvDsUserMeta.cast(l_user_meta.data)
                        if user_meta.base_meta.meta_type == pyds.nvds_get_user_meta_type("NVIDIA.DSANALYTICSOBJ.USER_META"):

                            user_meta_data = pyds.NvDsAnalyticsObjInfo.cast(user_meta.user_meta_data)
                            #if frame_number % numFrameToUpdate == 0:
                                #
                            if user_meta_data.dirStatus:
                               
                                #logger.info("Object {0} moving in direction: {1}".format(obj_meta.object_id, user_meta_data.dirStatus))
                                self.transmitFrame.allAnalyticItems[user_meta_data.dirStatus].IncreaseCountOfClass(self.pgie_classes_str[obj_meta.class_id])
                            if user_meta_data.lcStatus:
                                for itemName in user_meta_data.lcStatus:

                                    
                                    self.transmitFrame.allAnalyticItems[itemName].IncreaseCountOfClass(self.pgie_classes_str[obj_meta.class_id])
                                    #logger.info("Object {0} line crossing status: {1}".format(obj_meta.object_id, user_meta_data.lcStatus))
                            if user_meta_data.ocStatus:
                                for itemName in user_meta_data.ocStatus:
                                    
                                    self.transmitFrame.allAnalyticItems[itemName].IncreaseCountOfClass(self.pgie_classes_str[obj_meta.class_id])
                                    #logger.info("Object {0} overcrowding status: {1}".format(obj_meta.object_id, user_meta_data.ocStatus))
                            if user_meta_data.roiStatus:
                                for itemName in user_meta_data.roiStatus:

                                    self.transmitFrame.allAnalyticItems[itemName].IncreaseCountOfClass(self.pgie_classes_str[obj_meta.class_id])
                                    print("roi num:{}".format(self.transmitFrame.allAnalyticItems[itemName].parseCount))
                                    # if itemName == "vung_san":
                                    #     logger.info("ds: {}".format(self.transmitFrame.allAnalyticItems[itemName].parseCount))
                                # logger.info("Object {0} roi status: {1}".format(obj_meta.object_id, user_meta_data.roiStatus))
                    except StopIteration:
                        break
                    try:
                        l_user_meta = l_user_meta.next
                    except StopIteration:
                        break
                try: 
                    l_obj=l_obj.next
                except StopIteration:
                    break

            # Get meta data from 
            l_user = frame_meta.frame_user_meta_list
            
            while l_user:
                try:
                    user_meta = pyds.NvDsUserMeta.cast(l_user.data)
                    if user_meta.base_meta.meta_type == pyds.nvds_get_user_meta_type("NVIDIA.DSANALYTICSFRAME.USER_META"):
                        #idVal = 0
                        user_meta_data = pyds.NvDsAnalyticsFrameMeta.cast(user_meta.user_meta_data)
                        
                        if user_meta_data.objInROIcnt:
                            #
                            # logger.info("Objs in ROI: {0}".format(user_meta_data.objInROIcnt))
                            listName = list(user_meta_data.objInROIcnt.keys())
                            #idVal = self.transmitFrame.GetIDFromItemName(itemName = listName[0], type = "roi")
                            for analyticName, val in user_meta_data.objInROIcnt.items():
                                #self.transmitFrame.UpdateItemTotalCount(cameraID = idVal, type = "roi", itemName = key, newValue = val)
                                self.transmitFrame.allAnalyticItems[analyticName].totalCount = val
                                
                        if user_meta_data.objLCCumCnt:
                            for analyticName, val in user_meta_data.objLCCumCnt.items():
                                self.transmitFrame.allAnalyticItems[analyticName].totalCount = val
                                #self.transmitFrame.UpdateItemTotalCount(cameraID = idVal, type = "line", itemName = key, newValue = val)
                            # logger.info("Linecrossing Cumulative: {0}".format(user_meta_data.objLCCumCnt))
                        # if user_meta_data.objLCCurrCnt:
                            
                        #     #self.transmitFrame.UpdateItemTotalCount(cameraID = index, type = "line", itemName = user_meta_data.objLCCumCnt.keys()[0], newValue = user_meta_data.objLCCumCnt.vals()[0])
                        #     logger.info("Linecrossing Current Frame: {0}".format(user_meta_data.objLCCurrCnt))
                        if user_meta_data.ocStatus: logger.info("Overcrowding status: {0}".format(user_meta_data.ocStatus))

                    
                except StopIteration:
                    break
                try:
                    l_user = l_user.next
                except StopIteration:
                    break
            
            try:
                l_frame=l_frame.next
            except StopIteration:
                break
            
            
        self.copy_message = deepcopy(self.transmitFrame.Convert2Message(FullAnalyticItem2Dict()))
        self.transmitFrame.ResetAllData()

            #logger.info("#"*50)

        return Gst.PadProbeReturn.OK

    

    def create_source_bin(self,index,uri):
        def decodebin_child_added(child_proxy,Object,name,user_data):
            logger.info(f"Decodebin child added: {name}")
            if(name.find("decodebin") != -1):
                Object.connect("child-added",decodebin_child_added,user_data)
        def cb_newpad(decodebin, decoder_src_pad, data):
            logger.info("In cb_newpad\n")
            caps = decoder_src_pad.get_current_caps()
            gststruct = caps.get_structure(0)
            gstname = gststruct.get_name()
            source_bin = data
            features = caps.get_features(0)
            # Need to check if the pad created by the decodebin is for video and not
            # audio.
            if (gstname.find("video") != -1):
                # Link the decodebin pad only if decodebin has picked nvidia
                # decoder plugin nvdec_*. We do this by checking if the pad caps contain
                # NVMM memory features.
                if features.contains("memory:NVMM"):
                    # Get the source bin ghost pad
                    bin_ghost_pad = source_bin.get_static_pad("src")
                    if not bin_ghost_pad.set_target(decoder_src_pad):
                        sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
                else:
                    sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")
        logger.info(uri)
        logger.info("Creating source bin")

        # Create a source GstBin to abstract this bin's content from the rest of the
        # pipeline
        bin_name="source-bin-%02d" %index
        logger.info(bin_name)
        nbin=Gst.Bin.new(bin_name)
        if not nbin:
            sys.stderr.write(" Unable to create source bin \n")

        # Source element for reading from the uri.
        # We will use decodebin and let it figure out the container format of the
        # stream and the codec and plug the appropriate demux and decode plugins.
        uri_decode_bin=Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")
        if not uri_decode_bin:
            sys.stderr.write(" Unable to create uri decode bin \n")
        # We set the input uri to the source element
        uri_decode_bin.set_property("uri",uri)
        # Connect to the "pad-added" signal of the decodebin which generates a
        # callback once a new pad for raw data has beed created by the decodebin
        uri_decode_bin.connect("pad-added",cb_newpad,nbin)
        uri_decode_bin.connect("child-added",decodebin_child_added,nbin)

        # We need to create a ghost pad for the source bin which will act as a proxy
        # for the video decoder src pad. The ghost pad will not have a target right
        # now. Once the decode bin creates the video decoder and generates the
        # cb_newpad callback, we will set the ghost pad target to the video decoder
        # src pad.
        Gst.Bin.add(nbin,uri_decode_bin)
        bin_pad=nbin.add_pad(Gst.GhostPad.new_no_target("src",Gst.PadDirection.SRC))
        if not bin_pad:
            sys.stderr.write(" Failed to add ghost pad in source bin \n")
            return None
        return nbin
    

    def create_source_bin_test(self,index,uri):
        def decodebin_child_added(child_proxy,Object,name,user_data):
            logger.info(f"Decodebin child added: {name}")
            if(name.find("decodebin") != -1):
                Object.connect("child-added",decodebin_child_added,user_data)
        def cb_newpad(decodebin, decoder_src_pad, data):
            logger.info("In cb_newpad\n")
            caps = decoder_src_pad.get_current_caps()
            gststruct = caps.get_structure(0)
            gstname = gststruct.get_name()
            source_bin = data
            features = caps.get_features(0)
            # Need to check if the pad created by the decodebin is for video and not
            # audio.
            if (gstname.find("video") != -1):
                # Link the decodebin pad only if decodebin has picked nvidia
                # decoder plugin nvdec_*. We do this by checking if the pad caps contain
                # NVMM memory features.
                if features.contains("memory:NVMM"):
                    # Get the source bin ghost pad
                    bin_ghost_pad = source_bin.get_static_pad("src")
                    if not bin_ghost_pad.set_target(decoder_src_pad):
                        sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
                else:
                    sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")
        logger.info(uri)
        logger.info("Creating source bin")

        # Create a source GstBin to abstract this bin's content from the rest of the
        # pipeline
        bin_name="source-bin-%02d" %index
        logger.info(bin_name)
        nbin=Gst.Bin.new(bin_name)
        if not nbin:
            sys.stderr.write(" Unable to create source bin \n")

        # Source element for reading from the uri.
        # We will use decodebin and let it figure out the container format of the
        # stream and the codec and plug the appropriate demux and decode plugins.
        uri_decode_bin=Gst.ElementFactory.make("testsrcbin", "uri-decode-bin")
        if not uri_decode_bin:
            sys.stderr.write(" Unable to create uri decode bin \n")
        # We set the input uri to the source element
  
        # Connect to the "pad-added" signal of the decodebin which generates a
        # callback once a new pad for raw data has beed created by the decodebin
        uri_decode_bin.connect("pad-added",cb_newpad,nbin)
        uri_decode_bin.connect("child-added",decodebin_child_added,nbin)

        # We need to create a ghost pad for the source bin which will act as a proxy
        # for the video decoder src pad. The ghost pad will not have a target right
        # now. Once the decode bin creates the video decoder and generates the
        # cb_newpad callback, we will set the ghost pad target to the video decoder
        # src pad.
        Gst.Bin.add(nbin,uri_decode_bin)
        bin_pad=nbin.add_pad(Gst.GhostPad.new_no_target("src",Gst.PadDirection.SRC))
        if not bin_pad:
            sys.stderr.write(" Failed to add ghost pad in source bin \n")
            return None
        return nbin
    
   
    def AMQP_publisher(self):
        self.pre_frame = 0

        while(1):
            if self.frame_number!= 0 and self.frame_number%5 == 0:
                if self.frame_number != self.pre_frame:
                    if self.copy_message!= None:
                        self.sender.Send_data(self.copy_message)
                        self.pre_frame = self.frame_number
                        #print(self.copy_message)

    
            #logger.info(" [x] Sent %r:%r" % (severity, message))
            
    def run(self):
        number_sources = len(self.pipeline_config.sources.sources_input)

        # Standard GStreamer initialization
        Gst.init(None)

        # Create gstreamer elements */
        # Create Pipeline element that will form a connection of other elements
        logger.info("Creating Pipeline \n ")
        pipeline = Gst.Pipeline()
        is_live = False
        if not pipeline:
            sys.stderr.write(" Unable to create Pipeline \n")
        logger.info("Creating streamux \n ")
        # Create nvstreammux instance to fo_wrap_prob
        streammux = Streammux_element(self.pipeline_config.streammux).element
        pipeline.add(streammux)
        camera_check = Update_camera_status(server_IP = self.pipeline_config.sink_rtsp.rtsp_host, server_port = 7894)
        list_disconnect = camera_check.Check_disconnect_camera(CheckConnect_Response_ping)
        if number_sources == 0:
            sys.stderr.write("Please add stream RTSP to run")
            sys.exit(1)
        else:
            for i in range(number_sources):
                #os.mkdir(folder_name + "/stream_" + str(i))
                
                logger.info(f"Creating source_bin :{i}")
                uri_name = self.pipeline_config.sources.sources_input[i].uri
                if uri_name.find("rtsp://") == 0:
                    is_live = True
                logger.info(uri_name)
                if i in list_disconnect:
                    
                    source_bin = self.create_source_bin_test(i, "testbin://video,pattern=green,caps=[video/x-raw,width=1920,height=1080,framerate=30/1]")
                else:

                    source_bin = self.create_source_bin(i, uri_name)
                if not source_bin:
                    sys.stderr.write("Unable to create source bin \n")
                pipeline.add(source_bin)
                padname = "sink_%u" % i
                sinkpad = streammux.get_request_pad(padname)
                if not sinkpad:
                    sys.stderr.write("Unable to create sink pad bin \n")
                srcpad = source_bin.get_static_pad("src")
                if not srcpad:
                    sys.stderr.write("Unable to create src pad bin \n")
                srcpad.link(sinkpad)
        # Add nvvidconv1 and filter1 to convert the frames to RGBA
        # which is easier to work with in Python.
        
        nvvidconv1 = Create_element("nvvideoconvert", "convertor1").element
        caps1 = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA")
        filter1 = Create_element("capsfilter", "filter1").element
        filter1.set_property("caps", caps1)
        tiler = Tiler_element(self.pipeline_config.tiler).element

        nvvidconv = Create_element("nvvideoconvert", "convertor").element
        #Check if the hardware is jetson and Add transform layer.
    
        if (is_aarch64()):
            
            transform = Create_element("nvegltransform", "nvegl-transform").element
    
        sink = Sink_display_element(self.pipeline_config.sink_display).element
        nvosd = OSD_element(self.pipeline_config.osd).element
        pgie = Pgie_element(self.pipeline_config.pgie, number_sources).element
        # second_gie = Gst.ElementFactory.make("nvinfer", "seconf_nvinfer")
        # second_gie.set_property('config-file-path', 'dstest_imagedata_config.txt')

        #Create Tracker element
        tracker = Tracker_element(self.pipeline_config.tracker).element
        nvanalytics = Analytic_element(self.pipeline_config.analytic).element
        nvvideo_postOSD = Create_element("nvvideoconvert", "convertor_postosd").element

        tee = Gst.ElementFactory.make("tee", "tee")
        queue_screen = Gst.ElementFactory.make("queue", "queue_screen")
        queue_nvvid = Gst.ElementFactory.make("queue", "queue_nvvid")
        

        #Create queue data pipline
        queue1 = Gst.ElementFactory.make("queue", "queue1")
        if not queue1:
            logger.info("Unable to create queue1")
        
        if self.pipeline_config.sink_rtsp != None:
            logger.info(self.pipeline_config.sink_rtsp.rtsp_host)
            if func.Connected_to_network(self.pipeline_config.sink_rtsp.rtsp_host):
                encoder = Encoder_element(codec_type=self.pipeline_config.sink_rtsp.codec, bitrate = int(self.pipeline_config.sink_rtsp.bitrate)).element
                rtppay = Rtppay_element(codec_type=self.pipeline_config.sink_rtsp.codec).element
                sink_rtsp = Sink_RTSP_element(config_model = self.pipeline_config.sink_rtsp).element
                
            else:
                logger.critical("The network is not correct as set in the config. Change the network and Reset")

            #Set True when using preprocessng data step
            #pgie.set_property("input-tensor-meta", True)
        # if not is_aarch64():
        # #      # Use CUDA unified memory in the pipeline so frames
        # #     # can be easily accessed on CPU in Python.
        #      mem_type = int(pyds.NVBUF_MEM_CUDA_UNIFIED)
        #      streammux.set_property("nvbuf-memory-type", mem_type)
        #      nvvidconv.set_property("nvbuf-memory-type", mem_type)
        #      nvvidconv1.set_property("nvbuf-memory-type", mem_type)
        #      tiler.set_property("nvbuf-memory-type", mem_type)
        queue2=Gst.ElementFactory.make("queue","queue2")
        #queue3=Gst.ElementFactory.make("queue","queue3")
        
            # if not msgbroker:
            #     sys.stderr.write(" Unable to create msgbroker \n")

            # if topic is not None:
            #     msgbroker.set_property('sync', False)
            #     msgbroker.set_property('topic', topic)

        pipeline.add(tiler)
        pipeline.add(nvvidconv)
        pipeline.add(filter1)
        pipeline.add(nvvidconv1)
        pipeline.add(tee)
        pipeline.add(queue_nvvid)
        pipeline.add(queue_screen)
        pipeline.add(sink)
        pipeline.add(pgie)
        pipeline.add(tracker)
        pipeline.add(nvosd)
        pipeline.add(nvvideo_postOSD)
        pipeline.add(queue1)
        pipeline.add(queue2)
        pipeline.add(nvanalytics)
        #pipeline.add(second_gie)

        if self.pipeline_config.sink_rtsp != None:
            queue_rtsp = Create_element("queue", "queue_rtsp").element
            pipeline.add(sink_rtsp)
            pipeline.add(encoder)
            pipeline.add(rtppay)
            pipeline.add(queue_rtsp)

        if self.pipeline_config.msgbroker != None:
            if self.pipeline_config.msgbroker.type != "1":
                msgconv = Msgconv_element(config_model = self.pipeline_config.msgbroker).element
                #Add message broker element.
                msgbroker = Msgbroker_element(config_model = self.pipeline_config.msgbroker).element
                msgbroker = Gst.ElementFactory.make("nvmsgbroker", "nvms-broker")
                queue_msg = Create_element("queue", "queue_msg").element
                pipeline.add(msgconv)
                pipeline.add(msgbroker)
                pipeline.add(queue_msg)

            else:
                self.sender = AMQP(self.pipeline_config.msgbroker.msgbroker_file)
                amqp_thread = threading.Thread(target= self.AMQP_publisher)
                amqp_thread.start()
           

        
        logger.info("Linking elements in the Pipeline \n")
        streammux.link(queue1)
        queue1.link(pgie)
        pgie.link(tracker)
        #second_gie.link(tracker)
        tracker.link(nvanalytics)
        nvanalytics.link(nvvidconv1)
        nvvidconv1.link(filter1)
        filter1.link(tiler)
        tiler.link(nvvidconv)
        nvvidconv.link(nvosd)
        nvosd.link(tee)
        tee.link(queue_screen)
        queue_screen.link(sink)

        if self.pipeline_config.sink_rtsp != None:
            tee.link(queue_rtsp)
            queue_rtsp.link(nvvideo_postOSD)
            nvvideo_postOSD.link(encoder)
            encoder.link(rtppay)
            rtppay.link(sink_rtsp)
        
        if self.pipeline_config.msgbroker != None:
            if self.pipeline_config.msgbroker.type != "1":
                tee.link(queue_msg)
                queue_msg.link(msgconv)
                msgconv.link(msgbroker)
          


        # perf callback function to logger.info fps every 5 sec
        # create an event loop and feed gstreamer bus mesages to it
        loop = GLib.MainLoop()
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", bus_call, loop)
        tiler_sink_pad = tiler.get_static_pad("sink")
        if not tiler_sink_pad:
            sys.stderr.write(" Unable to get src pad \n")
        else:
            tiler_sink_pad.add_probe(Gst.PadProbeType.BUFFER, self.tiler_sink_pad_buffer_probe, 0)
            # perf callback function to logger.info fps every 5 sec
        # Start streaming
            # perf callback function to logger.info fps every 5 sec
            
        rtsp_port_num = int(self.pipeline_config.sink_rtsp.rtsp_port)
        server = GstRtspServer.RTSPServer.new()
        server.props.service = "%d" % rtsp_port_num
        server.attach(None)
        factory = GstRtspServer.RTSPMediaFactory.new()
        factory.set_launch(
            '( udpsrc name=pay0 port=%d buffer-size=524288 caps="application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 " )'
            % (5400, "H265")
        )
        factory.set_shared(True)
        server.get_mount_points().add_factory("/ds-test", factory)
        logger.info(
            "\n *** DeepStream: Launched RTSP Streaming at rtsp://localhost:%d/ds-test ***\n\n"
            % int(self.pipeline_config.sink_rtsp.rtsp_port)
        )
        
        # List the sources
        # logger.info("Now playing...")
        # for i, source in enumerate(args[:-1]):
        #     if i != 0:
        #         logger.info(i, ": ", source)

        logger.info("Starting pipeline \n")
        # start play back and listed to events		
        pipeline.set_state(Gst.State.PLAYING)
        # amqpRun = threading.Thread(target=streamAMQP())
        # amqpRun.start()
        try:
            loop.run()
        except:
            pass
        # cleanup
        logger.info("Exiting app\n")
        pipeline.set_state(Gst.State.NULL)


def main():
    parse = OptionParser()
    
    parse.add_option("-c", "--cfg-file", dest = "cfg_file",
                                action = "store", default = './config_file/init_config/config_camera.txt')
    (option, args) = parse.parse_args()
    config_file = option.cfg_file
    pipeline = Pipeline(config_file)
    sys.exit(pipeline.run())
    
if __name__ == '__main__':
    main()
    


    



