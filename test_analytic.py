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
import pika

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
from dataFormat import TransmitFrameConfig, BasicAnalyticItem2Dict, FullAnalyticItem2Dict
from copy import deepcopy
import logging

logging.basicConfig(level = logging.INFO,
                    format = "%(asctime)s %(levelname)s %(message)s")

# connection = pika.BlockingConnection(
# pika.ConnectionParameters(host='localhost'))
# channel = connection.channel()

# channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
credentials = pika.PlainCredentials(username = 'vietthang', password = "1999")
connect_param = pika.ConnectionParameters(
    host= '192.168.5.189',
    credentials=credentials
)
try:
    connection = pika.BlockingConnection(connect_param)
except:
    print("Cannot connect to AMQP server")
    sys.exit()

channel = connection.channel()
channel.exchange_declare(exchange = "ds_exchange", exchange_type='topic')


frame_count = {}
saved_count = {}
MAX_DISPLAY_LEN = 64
MAX_TIME_STAMP_LEN = 32
MUXER_OUTPUT_WIDTH = 1920
MUXER_OUTPUT_HEIGHT = 1080
MUXER_BATCH_TIMEOUT_USEC = 4000000
TILED_OUTPUT_WIDTH = 1920
TILED_OUTPUT_HEIGHT = int(540)
GST_CAPS_FEATURES_NVMM = "memory:NVMM"
MIN_CONFIDENCE = 0.3
MAX_CONFIDENCE = 0.4
UDPSINK_PORT_NUM = 5400
CLASS_VEHICLE = 0
CLASS_BICYCLE = 1
CLASS_PERSON = 2
CLASS_ROADSIGN= 3


CLASS_BOX = 0
MSCONV_CONFIG_FILE = "dstest4_msgconv_config.txt"
input_file = None
schema_type = 0
proto_lib = None
conn_str = "localhost;2181;testTopic"
cfg_file = None
topic = None
no_display = False
numFrameToUpdate = 5
pgie_classes_str = ["Vehicle", "TwoWheeler", "Person", "Roadsign"]
transmitFrame = TransmitFrameConfig("config_nvdsanalytics.txt", "deepstream_label.txt")
#transmitFrame = TransmitFrameConfig("config_nvdsanalytics.txt", "labelV5.txt")
#pgie_classes_str = ["Box"]

# CLASS_FORKLIFT = 0
# CLASS_PALLET = 1
# CLASS_PALLETTRUCK = 2
# CLASS_SMALLLIGAE = 3
# CLASS_STILLAGE = 4
frame_number = 0

class InputConfigData():

    def __init__(self):
        
        self.cfg_file = ''
        self.proto_lib = ''
        self.schema_type = ''
        self.stream = []
        self.conn_str = ''
        self.parse = OptionParser()
        self.parse.add_option("-c", "--cfg-file", dest = "cfg_file",
                                action = "store", default = '')
        self.parse.add_option("-p", "--proto-lib", dest = "proto_lib", action = "store", default = '')
        self.parse.add_option("-s", "--schema-type", dest= "schema_type", default = "0", action = "store")
        self.parse.add_option("-r", "--rstp", dest = "stream", action = "append")
        self.parse.add_option("", "--conn-str", dest = "conn_str")

    def SetInputFromArg(self):
        (option, args) = self.parse.parse_args()
        self.cfg_file = option.cfg_file
        self.conn_str = option.conn_str
        print("config file: %s" % self.cfg_file)
        self.proto_lib = option.proto_lib
        print("lib_file: %s" % self.proto_lib)
        self.stream = option.stream
        self.schema_type = option.schema_type
        

# Callback function for deep-copying an NvDsEventMsgMeta struct
def meta_copy_func(data, user_data):
    # Cast data to pyds.NvDsUserMeta
    user_meta = pyds.NvDsUserMeta.cast(data)
    src_meta_data = user_meta.user_meta_data
    # Cast src_meta_data to pyds.NvDsEventMsgMeta
    srcmeta = pyds.NvDsEventMsgMeta.cast(src_meta_data)
    # Duplicate the memory contents of srcmeta to dstmeta
    # First use pyds.get_ptr() to get the C address of srcmeta, then
    # use pyds.memdup() to allocate dstmeta and copy srcmeta into it.
    # pyds.memdup returns C address of the allocated duplicate.
    dstmeta_ptr = pyds.memdup(pyds.get_ptr(srcmeta),
                              sys.getsizeof(pyds.NvDsEventMsgMeta))
    # Cast the duplicated memory to pyds.NvDsEventMsgMeta
    dstmeta = pyds.NvDsEventMsgMeta.cast(dstmeta_ptr)
    
    # Duplicate contents of ts field. Note that reading srcmeat.ts
    # returns its C address. This allows to memory operations to be
    # performed on it.
    dstmeta.ts = pyds.memdup(srcmeta.ts, MAX_TIME_STAMP_LEN + 1)

    # Copy the sensorStr. This field is a string property. The getter (read)
    # returns its C address. The setter (write) takes string as input,
    # allocates a string buffer and copies the input string into it.
    # pyds.get_string() takes C address of a string and returns the reference
    # to a string object and the assignment inside the binder copies content.
    dstmeta.sensorStr = pyds.get_string(srcmeta.sensorStr)

    if srcmeta.objSignature.size > 0:
        dstmeta.objSignature.signature = pyds.memdup(
            srcmeta.objSignature.signature, srcmeta.objSignature.size)
        dstmeta.objSignature.size = srcmeta.objSignature.size

    if srcmeta.extMsgSize > 0:

        if srcmeta.objType == pyds.NvDsObjectType.NVDS_OBJECT_TYPE_PERSON:
            srcobj = pyds.NvDsPersonObject.cast(srcmeta.extMsg)
            obj = pyds.alloc_nvds_person_object()
            obj.age = srcobj.age
            obj.gender = pyds.get_string(srcobj.gender)
            obj.cap = pyds.get_string(srcobj.cap)
            obj.hair = pyds.get_string(srcobj.hair)
            obj.apparel = pyds.get_string(srcobj.apparel)
            dstmeta.extMsg = obj
            dstmeta.extMsgSize = sys.getsizeof(pyds.NvDsVehicleObject)
            
    return dstmeta


# Callback function for freeing an NvDsEventMsgMeta instance
def meta_free_func(data, user_data):
    user_meta = pyds.NvDsUserMeta.cast(data)
    srcmeta = pyds.NvDsEventMsgMeta.cast(user_meta.user_meta_data)

    # pyds.free_buffer takes C address of a buffer and frees the memory
    # It's a NOP if the address is NULL
    pyds.free_buffer(srcmeta.ts)
    pyds.free_buffer(srcmeta.sensorStr)

    if srcmeta.objSignature.size > 0:
        pyds.free_buffer(srcmeta.objSignature.signature)
        srcmeta.objSignature.size = 0

    if srcmeta.extMsgSize > 0:
        if srcmeta.objType == pyds.NvDsObjectType.NVDS_OBJECT_TYPE_PERSON:
            obj = pyds.NvDsPersonObject.cast(srcmeta.extMsg)
            pyds.free_buffer(obj.gender)
            pyds.free_buffer(obj.cap)
            pyds.free_buffer(obj.hair)
            pyds.free_buffer(obj.apparel)
        pyds.free_gbuffer(srcmeta.extMsg)
        srcmeta.extMsgSize = 0

def generate_vehicle_meta(data):
    obj = pyds.NvDsVehicleObject.cast(data)
    obj.type = "sedan"
    obj.color = "blue"
    obj.make = "Bugatti"
    obj.model = "M"
    obj.license = "XX1234"
    obj.region = "CA"
    return obj

def generate_person_meta(data,class_id,state, area):
    obj = pyds.NvDsPersonObject.cast(data)
    obj.age = class_id
    obj.cap = "ara"
    obj.hair = "black"
    obj.gender = "male"
    obj.apparel = "oi"
    return obj

# tiler_sink_pad_buffer_probe  will extract metadata received on tiler src pad
# and update params for drawing rectangle, object information etc.
def generate_event_msg_meta(data, class_id,state, area):
    meta = pyds.NvDsEventMsgMeta.cast(data)
    meta.sensorId = 0
    meta.placeId = 0
    meta.moduleId = 0
    meta.sensorStr = "sensor-0"
    meta.ts = pyds.alloc_buffer(MAX_TIME_STAMP_LEN + 1)
    pyds.generate_ts_rfc3339(meta.ts, MAX_TIME_STAMP_LEN)

    # This demonstrates how to attach custom objects.
    # Any custom object as per requirement can be generated and attached
    # like NvDsVehicleObject / NvDsPersonObject. Then that object should
    # be handled in payload generator library (nvmsgconv.cpp) accordingly.

    meta.type = pyds.NvDsEventType.NVDS_EVENT_ENTRY
    meta.objType = pyds.NvDsObjectType.NVDS_OBJECT_TYPE_PERSON
    meta.objClassId = class_id
    obj = pyds.alloc_nvds_person_object()
    obj = generate_person_meta(obj,class_id,state, area)
    meta.extMsg = obj
    meta.extMsgSize = sys.getsizeof(pyds.NvDsPersonObject)
    return meta

def tiler_sink_pad_buffer_probe(pad, info, u_data):
    frame_number=0
    num_rects=0
    
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return
   
    # Retrieve batch metadata from the gst_buffer
    # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
    # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list
    
    while l_frame:
        try:
            # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
            # The casting is done by pyds.NvDsFrameMeta.cast()
            # The casting also keeps ownership of the underlying memory
            # in the C code, so the Python garbage collector will leave
            # it alone.
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            #print("frame num: {}".format(frame_meta.frame_num))
        except StopIteration:
            break

        frame_number=frame_meta.frame_num
        l_obj=frame_meta.obj_meta_list
        num_rects = frame_meta.num_obj_meta
        obj_counter = {
        CLASS_VEHICLE :0,
        CLASS_BICYCLE : 1,
        CLASS_PERSON : 2,
        CLASS_ROADSIGN : 3
        }
        # obj_counter = {
        # CLASS_BOX :0

        # }
        
        #print("#"*50)
        
        while l_obj:
        
                #transmitFrame.ResetAllData()

            try: 
                # Note that l_obj.data needs a cast to pyds.NvDsObjectMeta
                # The casting is done by pyds.NvDsObjectMeta.cast()
                obj_meta=pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            obj_counter[obj_meta.class_id] += 1
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
                            #print("Object {0} moving in direction: {1}".format(obj_meta.object_id, user_meta_data.dirStatus))
                            transmitFrame.allAnalyticItems[user_meta_data.dirStatus].IncreaseCountOfClass(pgie_classes_str[obj_meta.class_id])
                        if user_meta_data.lcStatus:
                            for itemName in user_meta_data.lcStatus:
                                transmitFrame.allAnalyticItems[itemName].IncreaseCountOfClass(pgie_classes_str[obj_meta.class_id])
                            # print("Object {0} line crossing status: {1}".format(obj_meta.object_id, user_meta_data.lcStatus))
                        if user_meta_data.ocStatus:
                            for itemName in user_meta_data.ocStatus:
                                transmitFrame.allAnalyticItems[itemName].IncreaseCountOfClass(pgie_classes_str[obj_meta.class_id])
                            #print("Object {0} overcrowding status: {1}".format(obj_meta.object_id, user_meta_data.ocStatus))
                        if user_meta_data.roiStatus:
                            for itemName in user_meta_data.roiStatus:
                                transmitFrame.allAnalyticItems[itemName].IncreaseCountOfClass(pgie_classes_str[obj_meta.class_id])
                                # if itemName == "vung_san":
                                #     print("ds: {}".format(transmitFrame.allAnalyticItems[itemName].parseCount))
                            # print("Object {0} roi status: {1}".format(obj_meta.object_id, user_meta_data.roiStatus))
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
                    idVal = 0
                    user_meta_data = pyds.NvDsAnalyticsFrameMeta.cast(user_meta.user_meta_data)
                    
                    if user_meta_data.objInROIcnt:
                        #
                        # print("Objs in ROI: {0}".format(user_meta_data.objInROIcnt))
                        listName = list(user_meta_data.objInROIcnt.keys())
                        idVal = transmitFrame.GetIDFromItemName(itemName = listName[0], type = "roi")
                        for key, val in user_meta_data.objInROIcnt.items():
                            transmitFrame.UpdateItemTotalCount(cameraID = idVal, type = "roi", itemName = key, newValue = val)
            
                    if user_meta_data.objLCCumCnt:
                        for key, val in user_meta_data.objLCCumCnt.items():
                            transmitFrame.UpdateItemTotalCount(cameraID = idVal, type = "line", itemName = key, newValue = val)
                        # print("Linecrossing Cumulative: {0}".format(user_meta_data.objLCCumCnt))
                    # if user_meta_data.objLCCurrCnt:
                        
                    #     #transmitFrame.UpdateItemTotalCount(cameraID = index, type = "line", itemName = user_meta_data.objLCCumCnt.keys()[0], newValue = user_meta_data.objLCCumCnt.vals()[0])
                    #     print("Linecrossing Current Frame: {0}".format(user_meta_data.objLCCurrCnt))
                    if user_meta_data.ocStatus: print("Overcrowding status: {0}".format(user_meta_data.ocStatus))

                   
            except StopIteration:
                break
            try:
                l_user = l_user.next
            except StopIteration:
                break

        # if frame_number % numFrameToUpdate == 0:
        #     print(logging.info(""))
        #     msg_meta = pyds.alloc_nvds_event_msg_meta()
        #     msg_meta.frameId = frame_number

        #     msg_meta = generate_event_msg_meta(msg_meta, 0,"ROI", str(json.dumps(transmitFrame.Convert2JSONFormat(FullAnalyticItem2Dict()))))
        # #     #print("data {} /n".format(str(json.dumps(transmitFrame.Convert2JSONFormat(FullAnalyticItem2Dict())))))
        #     user_event_meta = pyds.nvds_acquire_user_meta_from_pool(
        #     batch_meta)
        #     if user_event_meta:
        #         user_event_meta.user_meta_data = msg_meta
        #         user_event_meta.base_meta.meta_type = pyds.NvDsMetaType.NVDS_EVENT_MSG_META
        # #     #     # Setting callbacks in the event msg meta. The bindings
        # #     #     # layer will wrap these callables in C functions.
        # #     #     # Currently only one set of callbacks is supported.
        #         pyds.user_copyfunc(user_event_meta, meta_copy_func)
        #         pyds.user_releasefunc(user_event_meta, meta_free_func)
        #         pyds.nvds_add_user_meta_to_frame(frame_meta,
        #                                         user_event_meta)
                
        #     else:
        #         print("Error in attaching event meta to buffer\n")
                #print("Object {0} roi status: {1}".format(obj_meta.object_id, user_meta_data.roiStatus))
            
            #print("Frame Number=", frame_number, "stream id=", frame_meta.pad_index, "Number of Objects=",num_rects,"Vehicle_count=",obj_counter[CLASS_PERSON],"Person_count=",obj_counter[CLASS_VEHICLE])
            # Update frame rate through this probe
        stream_index = "stream{0}".format(frame_meta.pad_index)
        
        
        # global perf_data
        # perf_data.update_fps(stream_index)
        
        try:
            l_frame=l_frame.next
        except StopIteration:
            break
        transmitFrame.ResetAllData()
        

        
        #print("#"*50)
        

    return Gst.PadProbeReturn.OK


def cb_newpad(decodebin, decoder_src_pad,data):
    print("In cb_newpad\n")
    caps=decoder_src_pad.get_current_caps()
    gststruct=caps.get_structure(0)
    gstname=gststruct.get_name()
    source_bin=data
    features=caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    print("gstname=",gstname)
    if(gstname.find("video")!=-1):
        # Link the decodebin pad only if decodebin has picked nvidia
        # decoder plugin nvdec_*. We do this by checking if the pad caps contain
        # NVMM memory features.
        print("features=",features)
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad=source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
        else:
            sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")

def decodebin_child_added(child_proxy,Object,name,user_data):
    print("Decodebin child added:", name, "\n")
    if(name.find("decodebin") != -1):
        Object.connect("child-added",decodebin_child_added,user_data)

def create_source_bin(index,uri):
    print("Creating source bin")

    # Create a source GstBin to abstract this bin's content from the rest of the
    # pipeline
    bin_name="source-bin-%02d" %index
    print(bin_name)
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
   

def cb_newpad(decodebin, decoder_src_pad, data):
    print("In cb_newpad\n")
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


def decodebin_child_added(child_proxy, Object, name, user_data):
    print("Decodebin child added:", name, "\n")
    if name.find("decodebin") != -1:
        Object.connect("child-added", decodebin_child_added, user_data)

    if "source" in name:
        source_element = child_proxy.get_by_name("source")
        if source_element.find_property('drop-on-latency') != None:
            Object.set_property("drop-on-latency", True)

def create_source_bin(index, uri):
    bin_name = "source-bin-%02d" % index
    print(bin_name)
    nbin = Gst.Bin.new(bin_name)
    if not nbin:
        sys.stderr.write(" Unable to create source bin \n")
    # Source element for reading from the uri.
    # We will use decodebin and let it figure out the container format of the
    # stream and the codec and plug the appropriate demux and decode plugins.
    uri_decode_bin = Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")
    if not uri_decode_bin:
        sys.stderr.write(" Unable to create uri decode bin \n")
    # We set the input uri to the source element
    uri_decode_bin.set_property("uri", uri)
    # Connect to the "pad-added" signal of the decodebin which generates a
    # callback once a new pad for raw data has beed created by the decodebin
    uri_decode_bin.connect("pad-added", cb_newpad, nbin)              
    uri_decode_bin.connect("child-added", decodebin_child_added, nbin)

    # We need to create a ghost pad for the source bin which will act as a proxy
    # for the video decoder src pad. The ghost pad will not have a target right
    # now. Once the decode bin creates the video decoder and generates the
    # cb_newpad callback, we will set the ghost pad target to the video decoder
    # src pad.
    Gst.Bin.add(nbin, uri_decode_bin)
    bin_pad = nbin.add_pad(
        Gst.GhostPad.new_no_target(
            "src", Gst.PadDirection.SRC))
    if not bin_pad:
        sys.stderr.write(" Failed to add ghost pad in source bin \n")
        return None
    return nbin

def AMQP_publisher():
    while(1):
        
        if frame_number % 10 == 0:
                channel.basic_publish(
            exchange='ds_exchange', routing_key='ds_topic', body=str(transmitFrame.Convert2JSONFormat(FullAnalyticItem2Dict())))
        
def main(args):
    # Check input arguments
    global enableAMQP
    enableAMQP = False
    

    parseInput = InputConfigData()
    parseInput.SetInputFromArg()
    amqp_thread = threading.Thread(target= AMQP_publisher)
    amqp_thread.start()
    
    listStream = parseInput.stream
    number_sources = len(listStream)
    proto_lib = parseInput.proto_lib
    cfg_file = parseInput.cfg_file
    conn_str = parseInput.conn_str
    schema_type = 0 if parseInput.schema_type == "0" else 1

    # global folder_name
    # folder_name = args[-1]
    # if path.exists(folder_name):
    #     sys.stderr.write("The output folder %s already exists. Please remove it first.\n" % folder_name)
    #     sys.exit(1)

    # os.mkdir(folder_name)
   
    # print("Frames will be saved in ", folder_name)
    # Standard GStreamer initialization
    Gst.init(None)
    pyds.register_user_copyfunc(meta_copy_func)
    pyds.register_user_releasefunc(meta_free_func)

    # Create gstreamer elements */
    # Create Pipeline element that will form a connection of other elements
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()
    is_live = False
    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")
    print("Creating streamux \n ")
    # Create nvstreammux instance to fo_wrap_prob
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    pipeline.add(streammux)
    if number_sources == 0:
        sys.stderr.write("Please add stream RTSP to run")
        sys.exit(1)
    else:
        for i in range(number_sources):
            #os.mkdir(folder_name + "/stream_" + str(i))
            frame_count["stream_" + str(i)] = 0
            saved_count["stream_" + str(i)] = 0
            print("Creating source_bin ", i, " \n ")
            uri_name = listStream[i]
            if uri_name.find("rtsp://") == 0:
                is_live = True
            source_bin = create_source_bin(i, uri_name)
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
    print("Creating nvvidconv1 \n ")
    nvvidconv1 = Gst.ElementFactory.make("nvvideoconvert", "convertor1")
    if not nvvidconv1:
        sys.stderr.write(" Unable to create nvvidconv1 \n")
    print("Creating filter1 \n ")
    caps1 = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA")
    filter1 = Gst.ElementFactory.make("capsfilter", "filter1")
    if not filter1:
        sys.stderr.write(" Unable to get the caps filter1 \n")
    filter1.set_property("caps", caps1)
    print("Creating tiler \n ")
    tiler = Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
    if not tiler:
        sys.stderr.write(" Unable to create tiler \n")
    print("Creating nvvidconv \n ")
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")
    print("Creating nvosd \n ")
  
    if (is_aarch64()):
        print("Creating transform \n ")
        transform = Gst.ElementFactory.make("nvegltransform", "nvegl-transform")
        if not transform:
            sys.stderr.write(" Unable to create transform \n")
    print("Creating EGLSink \n")
    sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
    sink.set_property("sync", 0)
    if not sink:
        sys.stderr.write(" Unable to create egl sink \n")
    if is_live:
        print("Atleast one of the sources is live")
        streammux.set_property('live-source', 1)
    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('batch-size', number_sources)
    streammux.set_property('batched-push-timeout', 50000)#batched-push-timeout = 1000000/FPS
    streammux.set_property('live-source', 1)
    tiler_rows = int(math.sqrt(number_sources))
    tiler_columns = int(math.ceil((1.0 * number_sources) / tiler_rows))
    tiler.set_property("rows", tiler_rows)
    tiler.set_property("columns", tiler_columns)
    tiler.set_property("width", TILED_OUTPUT_WIDTH)

    tiler.set_property("height", TILED_OUTPUT_HEIGHT * tiler_rows)
    sink.set_property("sync", 0)
    sink.set_property("qos", 0)
    #Creating on screan display
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    if not nvosd:
        print("Cannot create nvosd")
    tee = Gst.ElementFactory.make("tee", "tee")
    queue_screen = Gst.ElementFactory.make("queue", "queue_screen")
    queue_nvvid = Gst.ElementFactory.make("queue", "queue_nvvid")
    queue_rtsp = Gst.ElementFactory.make("queue", "queue_rtsp")
    #Create queue data pipline
    queue1 = Gst.ElementFactory.make("queue", "queue1")
    if not queue1:
        print("Unable to create queue1")
    encoder = Gst.ElementFactory.make("nvv4l2h265enc", "encoder")
    #encoder.set_property("bitrate", 6048)
    if not encoder:
        sys.stderr.write(" Unable to create encoder")
    rtppay = Gst.ElementFactory.make("rtph265pay", "rtppay")
    if not rtppay:
        sys.stderr.write("Unable to create rtppay")
    sink_rtsp = Gst.ElementFactory.make("udpsink", "udpsink")
    if not sink_rtsp:
        sys.stderr.write("Unable to create sink_rtsp")
    sink_rtsp.set_property("host", "224.224.255.255")
    sink_rtsp.set_property("port", UDPSINK_PORT_NUM)
    sink_rtsp.set_property("async", False)
    sink_rtsp.set_property("sync", 1)
    sink_rtsp.set_property("qos", 0)

    #post nvideo 
    nvvideo_postOSD = Gst.ElementFactory.make("nvvideoconvert", "convertor_postosd")
    if not nvvideo_postOSD:
        print("Unable to create nvvideo_postOSD")
    #inference
    print("Creating Pgie")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    
    if not pgie:
        sys.stderr.write("Unable to create pgie")
    pgie.set_property("config-file-path", "dstest_imagedata_config.txt")
    pgie.set_property("interval", 2)
    #pgie.set_property("config-file-path", "config_infer_primary.txt")
    #Create analytic element
    nvanalytics = Gst.ElementFactory.make("nvdsanalytics", "analytics")
    if not nvanalytics:
        sys.stderr.write("Unable to create nvanalytics")
    nvanalytics.set_property("config-file", "config_nvdsanalytics.txt")

    #Create Tracker element
    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    if not tracker:
        sys.stderr.write("Unable to create tracker")
     #Set properties of tracker
    config = configparser.ConfigParser()
    config.read('dsnvanalytics_tracker_config.txt')
    config.sections()

    for key in config['tracker']:
        if key == 'tracker-width' :
            tracker_width = config.getint('tracker', key)
            tracker.set_property('tracker-width', tracker_width)
        if key == 'tracker-height' :
            tracker_height = config.getint('tracker', key)
            tracker.set_property('tracker-height', tracker_height)
        if key == 'gpu-id' :
            tracker_gpu_id = config.getint('tracker', key)
            tracker.set_property('gpu_id', tracker_gpu_id)
        if key == 'll-lib-file' :
            tracker_ll_lib_file = config.get('tracker', key)
            tracker.set_property('ll-lib-file', tracker_ll_lib_file)
        if key == 'll-config-file' :
            tracker_ll_config_file = config.get('tracker', key)
            tracker.set_property('ll-config-file', tracker_ll_config_file)
        if key == 'enable-batch-process' :
            tracker_enable_batch_process = config.getint('tracker', key)
            tracker.set_property('enable_batch_process', tracker_enable_batch_process)
        if key == 'enable-past-frame' :
            tracker_enable_past_frame = config.getint('tracker', key)
            tracker.set_property('enable_past_frame', tracker_enable_past_frame)
    #Set True when using preprocessng data step
    #pgie.set_property("input-tensor-meta", True)
    pgie_batch_size = pgie.get_property("batch_size")
    if(pgie_batch_size != number_sources):
        pgie.set_property("batch_size", number_sources)
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
    queue4=Gst.ElementFactory.make("queue","queue4")
    queue5=Gst.ElementFactory.make("queue","queue5")
    queue6=Gst.ElementFactory.make("queue","queue6")
    queue7=Gst.ElementFactory.make("queue","queue7")
    queue8=Gst.ElementFactory.make("queue","queue8")
    queue9=Gst.ElementFactory.make("queue","queue9")
    queue10=Gst.ElementFactory.make("queue","queue10")
    queue11=Gst.ElementFactory.make("queue","queue11")

    #Add message broker element.
    msgconv = Gst.ElementFactory.make("nvmsgconv", "nvmsg-converter")
    if not msgconv:
        sys.stderr.write(" Unable to create msgconv \n")
    msgconv.set_property('config', MSCONV_CONFIG_FILE)
    msgconv.set_property('payload-type', schema_type)
    msgbroker = Gst.ElementFactory.make("nvmsgbroker", "nvms-broker")
    if not msgbroker:
        sys.stderr.write(" Unable to create msgbroker \n")
        
    msgbroker.set_property('proto-lib', proto_lib)
    msgbroker.set_property('conn-str', conn_str)

    if cfg_file is not None:
        msgbroker.set_property('config', cfg_file)

    if topic is not None:
        msgbroker.set_property('sync', False)
        msgbroker.set_property('topic', topic)



    print("Adding elements to Pipeline \n")
    pipeline.add(queue2)
    #pipeline.add(queue3)
    pipeline.add(queue4)
    pipeline.add(queue5)
    pipeline.add(queue6)
    pipeline.add(queue7)
    pipeline.add(queue8)
    pipeline.add(queue9)
    pipeline.add(queue10)
    pipeline.add(queue11)
    pipeline.add(tiler)
    pipeline.add(nvvidconv)
    pipeline.add(filter1)
    pipeline.add(nvvidconv1)
    pipeline.add(tee)
    pipeline.add(queue_nvvid)
    pipeline.add(queue_screen)
    pipeline.add(queue_rtsp)
    pipeline.add(sink_rtsp)
    pipeline.add(encoder)
    pipeline.add(rtppay)
    pipeline.add(sink)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(nvosd)
    pipeline.add(nvvideo_postOSD)
    pipeline.add(queue1)
    pipeline.add(nvanalytics)
    pipeline.add(msgconv)
    pipeline.add(msgbroker)
    print("Linking elements in the Pipeline \n")
    streammux.link(queue1)
    queue1.link(pgie)
    pgie.link(tracker)
    tracker.link(nvanalytics)
    nvanalytics.link(nvvidconv1)
    nvvidconv1.link(filter1)
    filter1.link(tiler)
    tiler.link(queue6)
    queue6.link(nvvidconv)
    nvvidconv.link(queue7)
    queue7.link(nvosd)
    nvosd.link(queue8)
    queue8.link(tee)
    tee.link(queue9)
    queue9.link(queue_screen)
    tee.link(queue_nvvid)
    queue_nvvid.link(nvvideo_postOSD)
    tee.link(queue11)
    queue11.link(msgconv)
    msgconv.link(msgbroker)
    nvvideo_postOSD.link(encoder)
    queue_screen.link(queue10)
    queue10.link(sink)
    encoder.link(rtppay)
    rtppay.link(sink_rtsp)
    # perf callback function to print fps every 5 sec
    # create an event loop and feed gstreamer bus mesages to it
    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)
    tiler_sink_pad = tiler.get_static_pad("sink")
    if not tiler_sink_pad:
        sys.stderr.write(" Unable to get src pad \n")
    else:
        tiler_sink_pad.add_probe(Gst.PadProbeType.BUFFER, tiler_sink_pad_buffer_probe, 0)
        # perf callback function to print fps every 5 sec
    # Start streaming
        # perf callback function to print fps every 5 sec
        
    rtsp_port_num = 8554
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
    print(
        "\n *** DeepStream: Launched RTSP Streaming at rtsp://localhost:%d/ds-test ***\n\n"
        % rtsp_port_num
    )
     
    # List the sources
    # print("Now playing...")
    # for i, source in enumerate(args[:-1]):
    #     if i != 0:
    #         print(i, ": ", source)

    print("Starting pipeline \n")
    # start play back and listed to events		
    pipeline.set_state(Gst.State.PLAYING)
    # amqpRun = threading.Thread(target=streamAMQP())
    # amqpRun.start()
    try:
        loop.run()
    except:
        pass
    # cleanup
    print("Exiting app\n")
    pipeline.set_state(Gst.State.NULL)
if __name__ == '__main__':
    sys.exit(main(sys.argv))