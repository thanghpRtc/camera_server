import gi
import configparser
gi.require_version('Gst', '1.0')
gi.require_version("GstRtspServer", "1.0")
from gi.repository import GLib, Gst, GstRtspServer
import configparser
from lib.pipeline_config_model import *
import logging
import pika

logging.basicConfig(level = logging.ERROR,
                    filename = '/home/rtc/deepstream_logging/deepstream_log.log',
                    format = "%(asctime)s %(levelname)s %(message)s")

class Tracker_element():
    def __init__(self, config_model: Tracker_model):
        self.element = Gst.ElementFactory.make("nvtracker", "tracker")
        if not self.element:
            logging.error("Unable to create tracker")
        logging.info("Create nvtracker")
        #Set property for tracker
        logging.info((f"tracker file: {config_model.file}"))
        tracker_config = configparser.ConfigParser()
        tracker_config.read(config_model.file)
        logging.info((f"tracker file: {tracker_config.sections()}"))
        tracker_config.sections()

        for key in tracker_config['tracker']:
            if key == 'tracker-width' :
                tracker_width = tracker_config.getint('tracker', key)
                self.element.set_property('tracker-width', tracker_width)
            if key == 'tracker-height' :
                tracker_height = tracker_config.getint('tracker', key)
                self.element.set_property('tracker-height', tracker_height)
            if key == 'gpu-id' :
                tracker_gpu_id = tracker_config.getint('tracker', key)
                self.element.set_property('gpu_id', tracker_gpu_id)
            if key == 'll-lib-file' :
                tracker_ll_lib_file = tracker_config.get('tracker', key)
                self.element.set_property('ll-lib-file', tracker_ll_lib_file)
            if key == 'll-config-file' :
                tracker_ll_config_file = tracker_config.get('tracker', key)
                self.element.set_property('ll-config-file', tracker_ll_config_file)
            if key == 'enable-batch-process' :
                tracker_enable_batch_process = tracker_config.getint('tracker', key)
                self.element.set_property('enable_batch_process', tracker_enable_batch_process)
            if key == 'enable-past-frame' :
                tracker_enable_past_frame = tracker_config.getint('tracker', key)
                self.element.set_property('enable_past_frame', tracker_enable_past_frame)

class Tiler_element():

    def __init__(self,config_model: Tiler_model):
        self.element = Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
        if not self.element:
            logging.error("Unable to create tiler")
        logging.info("Create nvmultistreamtiler")

        #Set tiler property
        self.element.set_property('width', int(config_model.width))
        self.element.set_property('height', int(config_model.height))
        self.element.set_property('rows', int(config_model.rows))
        self.element.set_property('columns', int(config_model.columns))


class Filter_element():

    def __init__(self):
        self.filter = Gst.ElementFactory.make("capsfilter", "filter1")
        if not self.filter:
            logging.error("Unable to create filter")
        logging.info("Create filter")


class Sink_RTSP_element():
    def __init__(self, config_model:Sink_rtsp_model):
        self.element = Gst.ElementFactory.make("udpsink", "udpsink")
        if not self.element:
            logging.error("Unable to create sink_rtsp")

        logging.info("Create sink_rtsp")
        # self.element.set_property("host",config_model.host)
        # self.element.set_property("port", int(config_model.rtsp_port))
        # self.element.set_property("async", False)
        # self.element.set_property("sync", int(config_model.sync))
        # self.element.set_property("qos", int(config_model.qos))
        self.element.set_property("host","224.224.255.255")
        self.element.set_property("port", 5400)
        self.element.set_property("async", False)
        self.element.set_property("sync", 1)
        self.element.set_property("qos", 0)
        self.rtsp_host = config_model.rtsp_host

class Analytic_element():
    def __init__(self, config_model: Analytic_model):
        self.element = Gst.ElementFactory.make("nvdsanalytics", "analytics")
        if not self.element:
            logging.error("Unable to create analytic")
        logging.info("Create analytic element")

        self.element.set_property("config-file", config_model.file)

class Streammux_element():
    def __init__(self,config_model:Streammux_model):
        self.element = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
        if not self.element:
            logging.error("Unable to create streammux")
        logging.info("Create streammux element")
        self.element.set_property("width", int(config_model.width))
        self.element.set_property("height", int(config_model.height))
        self.element.set_property("batch-size", int(config_model.batch_size))
        self.element.set_property("batched_push_timeout", int(config_model.batched_push_timeout))
        self.element.set_property("live-source", int(config_model.live_source))

class Pgie_element():
    def __init__(self, config_model:Pgie, num_sources:int):
        self.element = Gst.ElementFactory.make("nvinfer", "primary-inference")

        if not self.element:
            logging.error("Cannot create pgie")

        logging.info("Create Pgie element")
        self.element.set_property("config-file-path", config_model.file)
        pgie_batch_size = self.element.get_property("batch_size")

        if (pgie_batch_size != num_sources):
            self.element.set_property("batch_size", num_sources)

class VideoConverter_element():
    
    def __init__(self):
        self.element = Gst.ElementFactory.make("nvvideoconvert", "convertor")
        if not self.element:
            logging.error("Unable to create nvvidconv") 

        logging.info("Create nvvidconv")

class Create_element():
    def __init__(self, factory_name, name, detail="", add =True):
        
        logging.info(f"Create {factory_name} element")

        self.element = Gst.ElementFactory.make(factory_name, name)

        if not self.element:

            logging.error(f"Cannot create {factory_name} element")

        logging.info(f"Creating {factory_name} element")



class OSD_element():
    def __init__(self, config_model = OSD_model):
        self.element= Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
        if not self.element:
            logging.error("Cannot create pgie")
        logging.info("Create Pgie element")

        self.element.set_property('process-mode',int(config_model.process_mode))
        self.element.set_property('display-text',int(config_model.display_text))

class Sink_display_element():
    def __init__(self, config_model: Sink_display_model):
        self.element = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
        if not self.element:
            logging.error("Cannot create nveglglessink")
        logging.info("Create nveglglessink element")

        self.element.set_property("sync", int(config_model.sync))
        self.element.set_property("qos",int(config_model.qos))

class Encoder_element():
    def __init__(self, codec_type = "H265",bitrate = 4000000, is_aarch64 = False):
        if codec_type == "H264" or codec_type == "h264":
            self.element = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
            logging.info("Create H264 Encoder")

        elif codec_type == "H265" or codec_type == "h265":
            self.element = Gst.ElementFactory.make("nvv4l2h265enc", "encoder")
            logging.info("Create H265 Encoder")

        if not self.element:
            logging.error("Unable to create encoder")

        self.element.set_property("bitrate", bitrate)

        if is_aarch64 == True:
            self.element.set_property("preset-level", 1)
            self.element.set_property("insert-sps-pps", 1)
            self.element.set_property("bufapi -version",1)

class Rtppay_element():

    def __init__(self, codec_type = "H265"):
        if codec_type == "H264" or codec_type == "h264":
            self.element = Gst.ElementFactory.make("rtph264pay", "rtppay")
            logging.info("Creating H264 rtppay")
        elif codec_type == "H265" or codec_type == "h265":
            self.element = Gst.ElementFactory.make("rtph265pay", "rtppay")
            logging.info("Creating H265 rtppay")
        if not self.element:
            logging.error(" Unable to create rtppay")

class Msgconv_element():
    def __init__(self, config_model = Msgbroker_model):
        self.element = Gst.ElementFactory.make("nvmsgconv", "nvmsg-converter")
        if not self.element :
            logging.error(" Unable to create msgconv \n")
        self.element.set_property('config', config_model.msgconv_file)
        self.element.set_property('payload-type', 0)


class Msgbroker_element():
    def __init__(self, config_model = Msgbroker_model):
        self.element = Gst.ElementFactory.make("nvmsgbroker", "nvms-broker")
        if not self.element :
            logging.error(" Unable to create nvmsgbroker \n")

        self.element.set_property('proto-lib', config_model.lib_file)
        self.element.set_property('config', config_model.msgbroker_file)
        self.element.set_property('conn-str', "localhost;2181;testTopic")

        logging.info("create nvmsgbroker")
        


# class Deepstream_Pipeline():
#     def __init__(self):
#         self.pipeline = Gst.Pipeline()
#         #Create pipeline
#         if not self.pipeline:
#             logging.error("Unable to create pipeline \n")


#     def AddElement(self, element):
#         pass

