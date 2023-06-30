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
#  download_url="https://github.com/nnsuite/testcases/raw/master/DeepLearningModels/tensorflow-lite/pose_estimation"
#  wget ${download_url}/posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite
#  wget ${download_url}/point_labels.txt
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
      self.fullscreen = True

      self.VIDEO_WIDTH = 640
      self.VIDEO_HEIGHT = 480
      self.MODEL_INPUT_HEIGHT = 257
      self.MODEL_INPUT_WIDTH = 257
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
      cmd += f'glvideomixer name=mix sink_0::zorder=1 sink_1::zorder=2 ! glimagesink sync=false qos=false '

      cmd += f'v4l2src name=src device=/dev/video{self.CAM_ID} ! video/x-raw,width=2316,height=1746,format=UYVY ! tee name=t_raw '
      cmd += f't_raw. ! queue ! v4l2convert output-io-mode=dmabuf-import extra-controls="cid,rotate=90" ! video/x-raw,width={self.VIDEO_WIDTH},height={self.VIDEO_HEIGHT},format=RGB,pixel-aspect-ratio=1/1 ! '
      cmd += f'queue ! mix. '
      cmd += f't_raw. ! queue ! v4l2convert output-io-mode=dmabuf-import capture-io-mode=mmap extra-controls="cid,rotate=90" ! video/x-raw,width={self.MODEL_INPUT_WIDTH},height={self.MODEL_INPUT_HEIGHT},format=RGB,pixel-aspect-ratio=1/1 ! '
      cmd += f'queue ! tensor_converter ! '
      cmd += f'queue ! tensor_transform mode=arithmetic option=typecast:float32,add:-127.5,div:127.5 ! '

      if engine == 'neuronsdk':
        tensor = dla_converter(self.tflite_model, self.dla)
        cmd += f'queue ! tensor_filter framework=neuronsdk model={self.dla} {tensor} ! '
      elif engine == 'tflite':
        cpu_cores = find_cpu_cores()
        cmd += f'queue ! tensor_filter framework=tensorflow-lite model={self.tflite_model} custom=NumThreads:{cpu_cores} ! '
      elif engine == 'armnn':
        library = find_armnn_delegate_library()
        cmd += f'queue ! tensor_filter framework=tensorflow-lite model={self.tflite_model} custom=Delegate:External,ExtDelegateLib:{library},ExtDelegateKeyVal:backends#GpuAcc ! '

      cmd += f'queue ! tensor_decoder mode=pose_estimation option1={self.VIDEO_WIDTH}:{self.VIDEO_HEIGHT} option2={self.MODEL_INPUT_WIDTH}:{self.MODEL_INPUT_HEIGHT} option3=/usr/bin/nnstreamer-demo/point_labels.txt option4=heatmap-offset ! '
      cmd += f'queue ! mix. '

      self.pipeline = Gst.parse_launch(cmd)
      logging.info("pipeline: %s" % cmd)

  def run(self):
      logging.info("Run: Pose estimation.")

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
      tflite_model = 'posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite'
      dla = 'posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.dla'
      tflite_label = 'point_labels.txt'

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
