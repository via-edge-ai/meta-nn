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
#  wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/mobilenet_v1_1.0_224_quant_and_labels.zip
#  unzip mobilenet_v1_1.0_224_quant_and_labels.zip
#  rm mobilenet_v1_1.0_224_quant_and_labels.zip
#  mv labels_mobilenet_quant_v1_224.txt labels.txt
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
    self.MODEL_INPUT_HEIGHT = 224
    self.MODEL_INPUT_WIDTH = 224
    self.FULLSCREEN = 0

    # $ v4l2-ctl --list-devices
    # C922 Pro Stream Webcam (usb-11290000.xhci-1.2):
    #  /dev/video130
    #  /dev/video131
    #  /dev/media2
    self.CAM_ID = 0

    self.tflite_model = ''
    self.dla = ''
    self.tflite_labels = []
    self.current_label_index = -1
    self.new_label_index = -1

    if not self.tflite_init():
        raise Exception

    GObject.threads_init()
    Gst.init(argv)

  def build_pipeline(self, engine):
    cmd = ''
    cmd += f'v4l2src name=src device=/dev/video{self.CAM_ID} ! video/x-raw,width=2316,height=1746,format=UYVY ! tee name=t_raw '
    cmd += f't_raw. ! queue ! v4l2convert output-io-mode=dmabuf-import extra-controls="cid,rotate=90" ! video/x-raw,width={self.VIDEO_WIDTH},height={self.VIDEO_HEIGHT},format=RGB16,pixel-aspect-ratio=1/1 ! '
    cmd += f'queue ! textoverlay name=tensor_res font-desc=Sans,24 ! waylandsink sync=false qos=false fullscreen={self.FULLSCREEN} '
    cmd += f't_raw. ! queue ! v4l2convert output-io-mode=dmabuf-import capture-io-mode=mmap extra-controls="cid,rotate=90" ! video/x-raw,width={self.MODEL_INPUT_WIDTH},height={self.MODEL_INPUT_HEIGHT},format=RGB,pixel-aspect-ratio=1/1 ! '
    cmd += f'queue ! tensor_converter ! '

    if engine == 'neuronsdk':
      tensor = dla_converter(self.tflite_model, self.dla)
      cmd += f'tensor_filter framework=neuronsdk model={self.dla} {tensor} ! '
    elif engine == 'tflite':
      cpu_cores = find_cpu_cores()
      cmd += f'tensor_filter framework=tensorflow-lite model={self.tflite_model} custom=NumThreads:{cpu_cores} ! '
    elif engine == 'armnn':
      library = find_armnn_delegate_library()
      cmd += f'tensor_filter framework=tensorflow-lite model={self.tflite_model} custom=Delegate:External,ExtDelegateLib:{library},ExtDelegateKeyVal:backends#GpuAcc ! '

    cmd += f'tensor_sink name=tensor_sink'

    self.pipeline = Gst.parse_launch(cmd)
    logging.info("pipeline: %s" % cmd)


  def build_pipeline_dev(self):
      cpu_cores = find_cpu_cores()
      tensor = dla_converter(self.tflite_model, self.dla)
      library = find_armnn_delegate_library()

      cmd = ''

      self.pipeline = Gst.parse_launch(cmd)
      logging.info("pipeline: %s" % cmd)


  def on_new_data(self, sink, buffer):
    if self.running:
        for idx in range(buffer.n_memory()):
            mem = buffer.peek_memory(idx)
            result, mapinfo = mem.map(Gst.MapFlags.READ)
            if result:
                # update label index with max score
                self.update_top_label_index(mapinfo.data, mapinfo.size)
                mem.unmap(mapinfo)

  def on_timer_update_result(self):
    if self.running:
        if self.current_label_index != self.new_label_index:
            # update textoverlay
            self.current_label_index = self.new_label_index
            label = self.tflite_get_label(self.current_label_index)
            textoverlay = self.pipeline.get_by_name('tensor_res')
            textoverlay.set_property('text', label)
    return True

  def tflite_get_label(self, index):
    try:
        label = self.tflite_labels[index]
    except IndexError:
        label = ''
    return label

  def update_top_label_index(self, data, data_size):
    # -1 if failed to get max score index
    self.new_label_index = -1

    if data_size == len(self.tflite_labels):
        scores = [data[i] for i in range(data_size)]
        max_score = max(scores)
        if max_score > 0:
            self.new_label_index = scores.index(max_score)
    else:
        logging.error('unexpected data size [%d]', data_size)

  def run(self):
      logging.info("Run: Image classification.")

      # main loop
      self.loop = GObject.MainLoop()

      # bus and message callback
      bus = self.pipeline.get_bus()
      bus.add_signal_watch()
      bus.connect('message', self.on_bus_message)

      # tensor sink signal : new data callback
      tensor_sink = self.pipeline.get_by_name('tensor_sink')
      tensor_sink.connect('new-data', self.on_new_data)

      # timer to update result
      GObject.timeout_add(500, self.on_timer_update_result)

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
      tflite_model = 'mobilenet_v1_1.0_224_quant.tflite'
      dla = 'mobilenet_v1_1.0_224_quant.dla'
      tflite_label = 'labels.txt'
      current_folder = os.path.dirname(os.path.abspath(__file__))
      model_folder = os.path.join(current_folder, '')

      # check model file exists
      self.tflite_model = os.path.join(model_folder, tflite_model)
      self.dla = os.path.join(model_folder, dla)
      if not os.path.exists(self.tflite_model):
          logging.error('cannot find tflite model [%s]', self.tflite_model)
          return False

      # load labels
      label_path = os.path.join(model_folder, tflite_label)
      try:
          with open(label_path, 'r') as label_file:
              for line in label_file.readlines():
                  self.tflite_labels.append(line)
      except FileNotFoundError:
          logging.error('cannot find tflite label [%s]', label_path)
          return False

      logging.info('finished to load labels, total [%d]', len(self.tflite_labels))
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
