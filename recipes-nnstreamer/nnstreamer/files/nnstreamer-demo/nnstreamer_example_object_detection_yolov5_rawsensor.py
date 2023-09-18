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

    self.VIDEO_WIDTH = 720
    self.VIDEO_HEIGHT = 1280
    self.MODEL_INPUT_HEIGHT = 320
    self.MODEL_INPUT_WIDTH = 320
    self.FULLSCREEN = 0
    self.CAM_ROT = 0
    self.CAM_ID = 0

    self.tflite_model = ''
    self.dla = ''
    self.label_path = ''

    self.filter = None
    self.textoverlay = None
    self.invoke_ms = 0

    if not self.tflite_init():
        raise Exception

    GObject.threads_init()
    Gst.init(argv)

  def build_pipeline(self, engine):
    cmd = ''

    cmd += f'v4l2src name=src device=/dev/video{self.CAM_ID} ! video/x-raw,width=2048,height=1536,format=YUY2,framerate=30/1 ! tee name=t_raw '
    cmd += f't_raw. ! queue leaky=2 max-size-buffers=10 ! '
    cmd += f'v4l2convert output-io-mode=dmabuf-import extra-controls="cid,rotate={self.CAM_ROT}" ! video/x-raw,width={self.VIDEO_WIDTH},height={self.VIDEO_HEIGHT},format=ARGB,pixel-aspect-ratio=1/1 ! '

    cmd += f'glvideomixer name=mix sink_0::zorder=1 sink_1::zorder=2 latency=999999999 ! '

    if self.THROUGHPUT == '1':
      cmd += f'textoverlay name=info text="" font-desc=Sans,18 valignment=top ! '

    cmd += f'fpsdisplaysink name=sink text-overlay=false signal-fps-measurements=true sync=false video-sink="glimagesink sync=false qos=false" '

    cmd += f't_raw. ! queue leaky=2 max-size-buffers=2 ! '
    cmd += f'v4l2convert output-io-mode=dmabuf-import capture-io-mode=mmap extra-controls="cid,rotate={self.CAM_ROT}" ! video/x-raw,width={self.MODEL_INPUT_WIDTH},height={self.MODEL_INPUT_HEIGHT},format=RGB,pixel-aspect-ratio=1/1 ! '
    cmd += f'tensor_converter ! '

    if engine == 'neuronsdk':
      tensor = dla_converter(self.tflite_model, self.dla)
      cmd += f'tensor_filter framework=neuronsdk throughput={self.THROUGHPUT} name=nn model={self.dla} {tensor} ! '
    elif engine == 'tflite':
      cpu_cores = find_cpu_cores()
      cmd += f'tensor_filter framework=tensorflow-lite throughput={self.THROUGHPUT} name=nn model={self.tflite_model} custom=NumThreads:{cpu_cores} ! '
    elif engine == 'armnn':
      library = find_armnn_delegate_library()
      cmd += f'tensor_filter framework=tensorflow-lite throughput={self.THROUGHPUT} name=nn model={self.tflite_model} custom=Delegate:External,ExtDelegateLib:{library},ExtDelegateKeyVal:backends#GpuAcc ! '
    elif engine == 'nnapi':
      logging.error('Not support NNAPI')

    cmd += f'other/tensors,num_tensors=1,types=uint8,dimensions=85:6300:1:1,format=static ! '
    cmd += f'tensor_transform mode=arithmetic option=typecast:float32,add:-4.0,mul:0.0051498096 ! '
    cmd += f'tensor_decoder mode=bounding_boxes option1=yolov5 option2={self.tflite_label} option3=0 option4={self.VIDEO_WIDTH}:{self.VIDEO_HEIGHT} option5={self.MODEL_INPUT_WIDTH}:{self.MODEL_INPUT_HEIGHT} ! '
    cmd += f'mix. '

    self.pipeline = Gst.parse_launch(cmd)
    logging.info("pipeline: %s" % cmd)

  def on_buffer(self, pad, info):
      throughput = self.filter.get_property('throughput')
      if (throughput > 0):
        fps = (throughput/1000.0);
        self.invoke_ms = (1.0/fps) * 1000.0;
        logging.debug('[on_buffer] fps[%d]', fps)
        logging.debug('[on_buffer] time[%f] ms', self.invoke_ms)

      return Gst.PadProbeReturn.OK

  def on_fps_measurement(self, element, fps, droprate, avgfps):
      logging.debug("[on_fps_measurement]")
      new_text = f'Camera FPS: {avgfps:.2f}, Invoke Time(ms):{round(self.invoke_ms, 2)}'
      self.textoverlay.set_property('text', new_text)

  def run(self):
      logging.info("Run: Object detection.")

      # main loop
      self.loop = GObject.MainLoop()

      # bus and message callback
      bus = self.pipeline.get_bus()
      bus.add_signal_watch()
      bus.connect('message', self.on_bus_message)

      if self.THROUGHPUT == '1':
          self.filter = self.pipeline.get_by_name("nn")
          # tensor_filter src signal : buffer ready callback
          srcpad = self.filter.get_static_pad("src")
          srcpad.add_probe(Gst.PadProbeType.BUFFER, self.on_buffer)

          # textoverlay to display throughput information of tensor_filter
          self.textoverlay = self.pipeline.get_by_name('info')
          sink = self.pipeline.get_by_name('sink')
          sink.connect('fps-measurements', self.on_fps_measurement)

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
  args = argument_parser_init(True)

  example = Demo(sys.argv[1:])
  example.CAM_ID = args.cam
  example.VIDEO_WIDTH = args.width
  example.VIDEO_HEIGHT = args.height
  example.FULLSCREEN = args.fullscreen
  example.THROUGHPUT = args.throughput
  example.CAM_ROT = args.rot

  enable_performance(args.performance)

  example.build_pipeline(args.engine)
  example.run()
