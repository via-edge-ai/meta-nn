#!/usr/bin/env python

import os
import sys
import gi
import re
import logging
import argparse
import subprocess
import numpy as np

############################################################################
#
#  // Download model
#  mkdir -p nnstreamer-demo
#  cd nnstreamer-demo
#  download_url="https://github.com/nnsuite/testcases/raw/master/DeepLearningModels/tensorflow-lite/zero_dce_tflite"
#  wget ${download_url}/lite-model_zero-dce_1.tflite
#
#  // Push to device
#  adb push nnstreamer-demo /usr/bin/
#
############################################################################

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
from nnstreamer_example import *

from PIL import Image

class Demo:
  def __init__(self, argv=None):
      self.loop = None
      self.pipeline = None
      self.running = False

      self.IMG_WIDTH = 600
      self.IMG_HEIGHT = 400
      self.FULLSCREEN = 0

      self.tflite_model = ''
      self.dla = ''
      self.image_path = ''
      self.export_image = ''

      GObject.threads_init()
      Gst.init(argv)

  def build_pipeline(self, engine):
      if not self.tflite_init():
          raise Exception

      cmd = ''
      cmd += f'filesrc location={self.image_path} ! pngdec ! videoscale ! '
      cmd += f'videoconvert ! video/x-raw,width={self.IMG_WIDTH},height={self.IMG_HEIGHT},format=RGB ! tensor_converter ! '
      cmd += f'tensor_transform mode=arithmetic option=typecast:float32,add:0,div:255.0 ! '

      if engine == 'neuronsdk':
        self.export_image += '_neuronsdk.png'
        tensor = dla_converter(self.tflite_model, self.dla)
        cmd += f'tensor_filter framework=neuronsdk model={self.dla} {tensor} ! '
      elif engine == 'tflite':
        self.export_image += '_tflite.png'
        cpu_cores = find_cpu_cores()
        cmd += f'queue ! tensor_filter framework=tensorflow-lite model={self.tflite_model} custom=NumThreads:{cpu_cores} ! '
      elif engine == 'armnn':
        self.export_image + '_armnn.png'
        library = find_armnn_delegate_library()
        cmd += f'queue ! tensor_filter framework=tensorflow-lite model={self.tflite_model} custom=Delegate:External,ExtDelegateLib:{library},ExtDelegateKeyVal:backends#GpuAcc ! '
      elif engine == 'nnapi':
        self.export_image += '_nnapi.png'
        logging.error('Not support NNAPI')

      cmd += 'tensor_sink name=tensor_sink'

      self.pipeline = Gst.parse_launch(cmd)
      logging.info("pipeline: %s" % cmd)

  def run(self):
      logging.info("Run: Low light image enhancement.")

      # main loop
      self.loop = GObject.MainLoop()

      # bus and message callback
      bus = self.pipeline.get_bus()
      bus.add_signal_watch()
      bus.connect('message', self.on_bus_message)

      # tensor sink signal : new data callback
      tensor_sink = self.pipeline.get_by_name('tensor_sink')
      tensor_sink.connect('new-data', self.on_new_data)

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
      tflite_model = 'lite-model_zero-dce_1.tflite'
      dla = 'lite-model_zero-dce_1.dla'

      current_folder = os.path.dirname(os.path.abspath(__file__))
      model_folder = os.path.join(current_folder, '')

      self.tflite_model = os.path.join(model_folder, tflite_model)
      self.dla = os.path.join(model_folder, dla)
      if not os.path.exists(self.tflite_model):
          logging.error('cannot find tflite model [%s]', self.tflite_model)
          return False

      if not os.path.exists(self.image_path):
          logging.error('cannot find image [%s]', self.image_path)
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

  def on_new_data(self, sink, buffer):
      """Callback for tensor sink signal.
      :param sink: tensor sink element
      :param buffer: buffer from element
      :return: None
      """
      if self.running:
          for idx in range(buffer.n_memory()):
              mem = buffer.get_memory(idx)
              result, mapinfo = mem.map(Gst.MapFlags.READ)

              if result:
                  content_arr = np.frombuffer(mapinfo.data, dtype=np.float32)
                  content = np.reshape(content_arr,(self.IMG_HEIGHT, self.IMG_WIDTH, 3)) * 255.0
                  content = content.clip(0,255)
                  img = Image.fromarray(np.uint8(content))
                  img.save(self.export_image)
                  logging.info('export png file: %s', self.export_image)
                  img.show()
                  mem.unmap(mapinfo)
          self.loop.quit()

def argument_parser():
  available_engine=['TBD', 'tflite', 'armnn']
  available_platform=['NA', 'G1200', 'G700', 'G350']

  if find_nnapi_delegate_library() != 'null':
    available_engine[0] = 'nnapi'
  if find_neuron_library() != 'null':
    available_engine[0] = 'neuronsdk'

  parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument(
      '--engine',
      default=available_engine[0],
      choices=available_engine,
      help='Choose a backends to inference. Default: %s' % available_engine[0])

  parser.add_argument(
      '--img',
      default=None,
      help='Input a image file path .\n' +
           'Example: /usr/bin/nnstreamer-demo/original.png\n')

  parser.add_argument(
      '--export',
      default='low_light_enhancement',
      help='Input a filename for the saved png image\n' +
           'Example: low_light_enhancement\n')

  parser.add_argument(
      '--width',
      default=600,
      type=int,
      help='Input image file width, ex: 600')

  parser.add_argument(
      '--height',
      default=400,
      type=int,
      help='Input image file height, ex: 400')

  parser.add_argument(
      '--performance',
      default=available_platform[0],
      choices=available_platform,
      help='Select platform and make CPU/GPU/APU run under performance mode, ex: G1200')

  args = parser.parse_args()
  return args

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  args = argument_parser()

  example = Demo(sys.argv[1:])
  example.image_path = args.img
  example.IMG_WIDTH = args.width
  example.IMG_HEIGHT = args.height
  example.export_image = args.export

  performance_hint(args.performance)

  example.build_pipeline(args.engine)
  example.run()