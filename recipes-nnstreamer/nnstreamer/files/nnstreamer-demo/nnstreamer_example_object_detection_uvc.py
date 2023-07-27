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
#  // Download model
#  mkdir -p nnstreamer-demo
#  cd nnstreamer-demo
#  download_url="https://github.com/nnsuite/testcases/raw/master/DeepLearningModels/tensorflow-lite/ssd_mobilenet_v2_coco"
#  wget ${download_url}/ssd_mobilenet_v2_coco.tflite
#  wget ${download_url}/coco_labels_list.txt
#  wget ${download_url}/box_priors.txt
#
#  // Push to device
#  adb push nnstreamer-demo /usr/bin/
#
############################################################################

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
from nnstreamer_example import *

class Demo:
  def __init__(self, argv=None):
    self.loop = None
    self.pipeline = None
    self.running = False

    self.VIDEO_WIDTH = 640
    self.VIDEO_HEIGHT = 480
    self.MODEL_INPUT_HEIGHT = 300
    self.MODEL_INPUT_WIDTH = 300
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
    self.box_priors = ''

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
    cmd += f'tensor_transform mode=arithmetic option=typecast:float32,add:-127.5,div:127.5 ! '

    if engine == 'neuronsdk':
      tensor = dla_converter(self.tflite_model, self.dla)
      cmd += f'queue ! tensor_filter framework=neuronsdk model={self.dla} {tensor} ! '
    elif engine == 'tflite':
      cpu_cores = find_cpu_cores()
      cmd += f'queue ! tensor_filter framework=tensorflow-lite model={self.tflite_model} custom=NumThreads:{cpu_cores} ! '
    elif engine == 'armnn':
      library = find_armnn_delegate_library()
      cmd += f'queue ! tensor_filter framework=tensorflow-lite model={self.tflite_model} custom=Delegate:External,ExtDelegateLib:{library},ExtDelegateKeyVal:backends#GpuAcc ! '
    elif engine == 'nnapi':
      logging.error('Not support NNAPI')

    cmd += f'tensor_decoder mode=bounding_boxes option1=mobilenet-ssd option2={self.label_path} option3={self.box_priors} option4={self.VIDEO_WIDTH}:{self.VIDEO_HEIGHT} option5={self.MODEL_INPUT_WIDTH}:{self.MODEL_INPUT_HEIGHT} ! '
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
      tflite_model = 'ssd_mobilenet_v2_coco.tflite'
      dla = 'ssd_mobilenet_v2_coco.dla'
      tflite_label = 'coco_labels_list.txt'
      tflite_box_priors = 'box_priors.txt'

      current_folder = os.path.dirname(os.path.abspath(__file__))
      model_folder = os.path.join(current_folder, '')

      self.tflite_model = os.path.join(model_folder, tflite_model)
      self.dla = os.path.join(model_folder, dla)
      if not os.path.exists(self.tflite_model):
          logging.error('cannot find tflite model [%s]', self.tflite_model)
          return False

      self.label_path = os.path.join(model_folder, tflite_label)
      if not os.path.exists(self.label_path):
          logging.error('cannot find point label [%s]', self.label_path)
          return False

      self.box_priors = os.path.join(model_folder, tflite_box_priors)
      if not os.path.exists(self.box_priors):
          logging.error('cannot find box priors file [%s]', self.box_priors)
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
