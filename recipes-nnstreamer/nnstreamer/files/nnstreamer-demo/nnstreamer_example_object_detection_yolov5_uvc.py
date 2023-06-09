#!/usr/bin/env python

import os
import sys
import gi
import re
import logging
import argparse
import subprocess

############################################################################
#
#  // Install yolov5
#  git clone https://github.com/ultralytics/yolov5
#  cd yolov5
#  pip install -r requirements.txt
#
#  // Export to tflite and torchscript model
#  python export.py --weights=yolov5s.pt --img=320 --include tflite torchscript
#  ls
#  ... yolov5s.torchscript yolov5s-fp16.tflite ...
#
#  // Export to quantized tflite model
#  python export.py --weights=yolov5s.pt --img=320 --include tflite --int8
#  ... yolov5s-int8.tflite ...
#
#  // Push to device
#  adb push yolov5s-int8.tflite /usr/bin/nnstreamer-demo
#  adb push yolov5s-fp16.tflite /usr/bin/nnstreamer-demo
#
############################################################################

gi.require_version('Gst', '1.0')
gi.require_version('GstGL', '1.0')

from gi.repository import Gst, GstGL, GObject
from nnstreamer_example import *

class Demo:
  def __init__(self, argv=None):
    self.loop = None
    self.pipeline = None
    self.running = False

    self.VIDEO_WIDTH = 640
    self.VIDEO_HEIGHT = 480
    self.MODEL_INPUT_HEIGHT = 320
    self.MODEL_INPUT_WIDTH = 320
    self.FULLSCREEN = 0

    # $ v4l2-ctl --list-devices
    # C922 Pro Stream Webcam (usb-11290000.xhci-1.2):
    #  /dev/video130
    #  /dev/video131
    #  /dev/media2
    self.CAM_ID = 0

    self.tflite_model = ''
    self.dla = ''
    self.label_path = ''
    
    if not self.tflite_init():
        raise Exception

    GObject.threads_init()
    Gst.init(argv)

  def build_pipeline(self, engine):
    cmd = ''
    cmd += f'v4l2src name=src device=/dev/video{self.CAM_ID} io-mode=mmap ! video/x-raw,width={self.VIDEO_WIDTH},height={self.VIDEO_HEIGHT},format=YUY2 ! tee name=t_raw '
    #cmd += f't_raw. ! queue leaky=2 max-size-buffers=10 ! compositor name=mix sink_0::zorder=1 sink_1::zorder=2 ! waylandsink sync=false fullscreen={self.FULLSCREEN} '
    cmd += f't_raw. ! queue leaky=2 max-size-buffers=10 ! compositor name=mix sink_0::zorder=1 sink_1::zorder=2 ! fpsdisplaysink sync=false video-sink="waylandsink sync=false fullscreen={self.FULLSCREEN}" '

    cmd += f't_raw. ! queue leaky=2 max-size-buffers=2 ! videoconvert ! videoscale ! video/x-raw,width={self.MODEL_INPUT_WIDTH},height={self.MODEL_INPUT_HEIGHT},format=RGB ! tensor_converter ! '

    if engine == 'neuronsdk':
      tensor = dla_converter(self.tflite_model, self.dla)
      cmd += f'tensor_filter framework=neuronsdk model={self.dla} {tensor} ! '
    elif engine == 'tflite':
      cpu_cores = find_cpu_cores()
      cmd += f'tensor_filter framework=tensorflow-lite model={self.tflite_model} custom=NumThreads:{cpu_cores} ! '
    elif engine == 'armnn':
      library = find_armnn_delegate_library()
      cmd += f'tensor_filter framework=tensorflow-lite model={self.tflite_model} custom=Delegate:External,ExtDelegateLib:{library},ExtDelegateKeyVal:backends#GpuAcc ! '
    elif engine == 'nnapi':
      logging.error('Not support NNAPI')

    cmd += f'other/tensors,num_tensors=1,types=uint8,dimensions=85:6300:1:1,format=static ! '
    cmd += f'tensor_transform mode=arithmetic option=typecast:float32,add:-4.0,mul:0.0051498096 ! '
    cmd += f'tensor_decoder mode=bounding_boxes option1=yolov5 option2={self.tflite_label} option3=0 option4={self.VIDEO_WIDTH}:{self.VIDEO_HEIGHT} option5={self.MODEL_INPUT_WIDTH}:{self.MODEL_INPUT_HEIGHT} ! '
    cmd += f'queue leaky=2 max-size-buffers=2 ! mix. '

    self.pipeline = Gst.parse_launch(cmd)
    logging.info("pipeline: %s" % cmd)

  def run(self):
      logging.info("Run: Object detection.")

      # main loop
      self.loop = GObject.MainLoop()

      # bus and message callback
      bus = self.pipeline.get_bus()
      bus.add_signal_watch()
      bus.connect('message', self.on_bus_message)

      # start pipeline
      self.pipeline.set_state(Gst.State.PLAYING)
      self.running = True

      # run main loop
      self.loop.run()

      # quit when received eos or error message
      self.running = False
      self.pipeline.set_state(Gst.State.NULL)

      bus.remove_signal_watch()

  def tflite_init(self):
      tflite_model = 'yolov5s-int8.tflite'
      dla = 'yolov5s-int8.dla'
      tflite_label = 'coco.txt'

      current_folder = os.path.dirname(os.path.abspath(__file__))
      model_folder = os.path.join(current_folder, '')

      self.tflite_model = os.path.join(model_folder, tflite_model)
      self.dla = os.path.join(model_folder, dla)
      if not os.path.exists(self.tflite_model):
          logging.error('cannot find tflite model [%s]', self.tflite_model)
          return False

      self.tflite_label = os.path.join(model_folder, tflite_label)
      if not os.path.exists(self.tflite_label):
          logging.error('cannot find label [%s]', self.tflite_label)
          return False

      return True

  def on_bus_message(self, bus, message):
      if message.type == Gst.MessageType.EOS:
          logging.info('received eos message')
          self.loop.quit()
      elif message.type == Gst.MessageType.ERROR:
          error, debug = message.parse_error()
          logging.warning('[error] %s : %s', error.message, debug)
          self.loop.quit()
      elif message.type == Gst.MessageType.WARNING:
          error, debug = message.parse_warning()
          logging.warning('[warning] %s : %s', error.message, debug)
      elif message.type == Gst.MessageType.STREAM_START:
          logging.info('received start message')
      elif message.type == Gst.MessageType.QOS:
          data_format, processed, dropped = message.parse_qos_stats()
          format_str = Gst.Format.get_name(data_format)
          logging.info('[qos] format[%s] processed[%d] dropped[%d]', format_str, processed, dropped)

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  args = argument_parser_init()
  
  example = Demo(sys.argv[1:])
  example.CAM_ID = args.cam
  example.VIDEO_WIDTH = args.width
  example.VIDEO_HEIGHT = args.height
  example.FULLSCREEN = args.fullscreen

  performance_hint(args.performance)

  example.build_pipeline(args.engine)
  example.run()
