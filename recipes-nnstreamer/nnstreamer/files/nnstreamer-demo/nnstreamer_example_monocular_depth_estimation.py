#!/usr/bin/env python

import os
import sys
import gi
import logging
import numpy as np
import cv2
import time
import queue

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
from nnstreamer_example import *

class Demo:
    def __init__(self, argv=None):
        self.loop = None
        self.pipeline = None
        self.running = False
        self.appsink = None
        self.last_frame_time = time.time()
        self.fps = 0.0

        self.VIDEO_WIDTH = 640
        self.VIDEO_HEIGHT = 480
        self.MODEL_INPUT_HEIGHT = 256
        self.MODEL_INPUT_WIDTH = 256
        self.CAM_ID = 0
        self.frame_queue = queue.Queue()

        self.tflite_model = ''
        self.dla = ''


        if not self.tflite_init():
            raise Exception("Failed to initialize the TFLite model.")

        Gst.init(argv)

    def tflite_init(self):

        tflite_model = 'midas.tflite'
        dla = 'midas.dla'

        current_folder = os.path.dirname(os.path.abspath(__file__))
        model_folder = os.path.join(current_folder, '')
        self.tflite_model = os.path.join(model_folder, tflite_model)
        self.dla = os.path.join(model_folder, dla)
        if not os.path.exists(self.tflite_model):
            logging.error('Cannot find TFLite model [%s]', self.tflite_model)
            return False
        return True

    def build_pipeline(self, engine):
        cmd = ''

        if self.cam_type == 'uvc':
            cmd = f'v4l2src name=src device=/dev/video{self.CAM_ID} ! video/x-raw,format=YUY2,width={self.VIDEO_WIDTH},height={self.VIDEO_HEIGHT},framerate=30/1 ! '
        elif self.cam_type == 'yuvsensor':
            cmd += f'v4l2src name=src device=/dev/video{self.CAM_ID} ! video/x-raw,width=1920,height=1080,format=UYVY ! '
        elif self.cam_type == 'rawsensor':
            cmd += f'v4l2src name=src device=/dev/video{self.CAM_ID} ! video/x-raw,width=2048,height=1536,format=YUY2 ! '  
        
        if self.cam_type == 'uvc':
            cmd += f'videoconvert ! videoscale ! video/x-raw,format=RGB,width={self.MODEL_INPUT_WIDTH},height={self.MODEL_INPUT_HEIGHT} ! ' 
        else:
            cmd += f'v4l2convert output-io-mode=dmabuf-import capture-io-mode=mmap extra-controls="cid,rotate={self.CAM_ROT}" ! video/x-raw,width={self.MODEL_INPUT_WIDTH},height={self.MODEL_INPUT_HEIGHT},format=RGB,pixel-aspect-ratio=1/1 ! '
        
        cmd += f'tensor_converter ! '  # Convert the video frame to tensor
        
        cmd += f'tensor_transform mode=arithmetic option=typecast:float32,add:-127.5,div:127.5 ! ' # Transform the tensor

        # Select the engine for execution

        if engine == 'neuronsdk':
            tensor = dla_converter(self.tflite_model, self.dla)
            cmd += f'tensor_filter framework=neuronsdk throughput={self.THROUGHPUT} model={self.dla} {tensor} ! '

        elif engine == 'tflite':
            cpu_cores = find_cpu_cores()
            cmd += f'tensor_filter framework=tensorflow-lite throughput={self.THROUGHPUT} model={self.tflite_model} custom=NumThreads:{cpu_cores} ! '
        
        elif engine == 'armnn':
            library = find_armnn_delegate_library()
            cmd += f'tensor_filter framework=tensorflow-lite throughput={self.THROUGHPUT} name=nn model={self.tflite_model} custom=Delegate:External,ExtDelegateLib:{library},ExtDelegateKeyVal:backends#GpuAcc ! '
        
        elif engine == 'nnapi':
            library = find_nnapi_delegate_library()
            cmd += f'tensor_filter framework=tensorflow-lite throughput={self.THROUGHPUT} name=nn model={self.tflite_model} custom=Delegate:External,ExtDelegateLib:{library} ! '
    
        cmd += f'appsink name=sink emit-signals=True max-buffers=1 drop=True sync=False'
        self.pipeline = Gst.parse_launch(cmd)
        logging.info("Pipeline: %s", cmd)

        # Get the appsink element
        self.appsink = self.pipeline.get_by_name('sink')
        
        # Connect the 'new-sample' signal to the callback function
        self.appsink.connect('new-sample', self.new_sample)
        self.appsink.set_property('emit-signals', True)
        
    def new_sample(self, sink):
        # new_sample callback to process each frame and display

        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        self.last_frame_time = current_time
        if elapsed > 0:
            self.fps = 1.0 / elapsed

        sample = sink.emit('pull-sample')
        if sample:
            buffer = sample.get_buffer()
            success, mapinfo = buffer.map(Gst.MapFlags.READ)
            if success:
                try:
                    data = np.frombuffer(mapinfo.data, dtype=np.float32)
                    depth_map = data.reshape((self.MODEL_INPUT_HEIGHT, self.MODEL_INPUT_WIDTH))
                    depth_map_visual = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX)
                    depth_map_visual = np.uint8(depth_map_visual)
                    depth_map_visual = cv2.resize(depth_map_visual, (self.VIDEO_WIDTH, self.VIDEO_HEIGHT), interpolation=cv2.INTER_CUBIC)
                    depth_map_visual = cv2.applyColorMap(depth_map_visual, cv2.COLORMAP_MAGMA)
                    cv2.putText(depth_map_visual, f'FPS: {self.fps:.2f}', (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    # Put the frame into the queue
                    self.frame_queue.put(depth_map_visual)
                finally:
                    buffer.unmap(mapinfo)
        return Gst.FlowReturn.OK

    def display_frame_from_queue(self):
        # Check if there are frames in the queue and display them
        try:
            while not self.frame_queue.empty():
                frame = self.frame_queue.get_nowait()
                cv2.imshow('Depth Map', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.loop.quit()
                    return False  # Stop the GLib timeout
        except queue.Empty:
            pass
        return True  # Continue the GLib timeout   

    def run(self):
        logging.info("Running MiDaS model for depth estimation")

        # Main loop
        self.loop = GLib.MainLoop()

        # Bus and message callback
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_bus_message)

        # Start pipeline
        self.pipeline.set_state(Gst.State.PLAYING)
        self.running = True

        # check queue for new frame and display using OpenCV
        GLib.timeout_add(30, self.display_frame_from_queue)

        # Run main loop
        self.loop.run()

        # Quit when received eos or error message
        self.running = False
        self.pipeline.set_state(Gst.State.NULL)

        bus.remove_signal_watch()
        #cv2.destroyAllWindows()

    def on_bus_message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            logging.info('Received EOS message')
            self.loop.quit()
        elif message.type == Gst.MessageType.ERROR:
            error, debug = message.parse_error()
            logging.warning('Error: %s: %s', error.message, debug)
            self.loop.quit()
        elif message.type == Gst.MessageType.WARNING:
            error, debug = message.parse_warning()
            logging.warning('Warning: %s: %s', error.message, debug)

    def check_opencv_events(self):
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.loop.quit()
        return True

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = argument_parser_init()

    # Create an instance of the Demo class
  
    example = Demo(sys.argv[1:])
    example.CAM_ID = args.cam
    example.VIDEO_WIDTH = args.width
    example.VIDEO_HEIGHT = args.height
    example.FULLSCREEN = args.fullscreen
    example.THROUGHPUT = args.throughput
    example.CAM_ROT = args.rot
    example.cam_type = args.cam_type

    example.VIDEO_WIDTH = 640
    example.VIDEO_HEIGHT = 480

    enable_performance(args.performance)

    # Build the GStreamer pipeline
    example.build_pipeline(args.engine)

    # Run the main loop
    example.run()