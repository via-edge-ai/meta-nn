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
from gi.repository import Gst, GLib
from nnstreamer_example import *

class Demo:
  def __init__(self, argv=None):
    self.loop = None
    self.pipeline = None
    self.running = False

    self.VIDEO_WIDTH = 720
    self.VIDEO_HEIGHT = 1280
    self.MODEL_INPUT_HEIGHT = 300
    self.MODEL_INPUT_WIDTH = 300
    self.FULLSCREEN = 0
    self.CAM_ROT = 0
    self.CAM_ID = 0

    self.tflite_model = ''
    self.dla = ''
    self.label_path = ''
    self.box_priors = ''

    self.filter = None
    self.textoverlay = None
    self.invoke_ms = 0

    if not self.tflite_init():
        raise Exception

    Gst.init(argv)

  def build_pipeline(self, engine):
    cmd = ''
    if self.cam_type == 'uvc':
        cmd += f'v4l2src name=src device=/dev/video{self.CAM_ID} io-mode=mmap ! video/x-raw,width={self.VIDEO_WIDTH},height={self.VIDEO_HEIGHT},format=YUY2 ! tee name=t_raw '
    elif self.cam_type == 'yuvsensor':
        cmd += f'v4l2src name=src device=/dev/video{self.CAM_ID} ! video/x-raw,width=1920,height=1080,format=UYVY ! tee name=t_raw '
    elif self.cam_type == 'rawsensor':
        cmd += f'v4l2src name=src device=/dev/video{self.CAM_ID} ! video/x-raw,width=2048,height=1536,format=YUY2 ! tee name=t_raw '

    cmd += f't_raw. ! queue leaky=2 max-size-buffers=10 ! '

    if self.cam_type != 'uvc':
        cmd += f'v4l2convert output-io-mode=dmabuf-import extra-controls="cid,rotate={self.CAM_ROT}" ! video/x-raw,width={self.VIDEO_WIDTH},height={self.VIDEO_HEIGHT},format=ARGB,pixel-aspect-ratio=1/1 ! '
        cmd += f'glvideomixer name=mix sink_0::zorder=1 sink_1::zorder=2 latency=999999999 ! '
    if self.cam_type == 'uvc':
        cmd += f'compositor name=mix sink_0::zorder=1 sink_1::zorder=2 latency=999999999 ! '
    if self.THROUGHPUT == '1':
      cmd += f'textoverlay name=info text="" font-desc=Sans,18 valignment=top ! '

    if self.cam_type == 'uvc':
        cmd += f'fpsdisplaysink name=sink text-overlay=false signal-fps-measurements=true sync=false video-sink="waylandsink sync=false qos=false fullscreen={self.FULLSCREEN}"'
    else:
        cmd += f'fpsdisplaysink name=sink text-overlay=false signal-fps-measurements=true sync=false video-sink="glimagesink sync=false qos=false" '

    cmd += f't_raw. ! queue leaky=2 max-size-buffers=2 ! '

    if self.cam_type == 'uvc':
        cmd += f'videoconvert ! videoscale ! video/x-raw,width={self.MODEL_INPUT_WIDTH},height={self.MODEL_INPUT_HEIGHT},format=RGB ! '
    else:
        cmd += f'v4l2convert output-io-mode=dmabuf-import capture-io-mode=mmap extra-controls="cid,rotate={self.CAM_ROT}" ! video/x-raw,width={self.MODEL_INPUT_WIDTH},height={self.MODEL_INPUT_HEIGHT},format=RGB,pixel-aspect-ratio=1/1 ! '
    cmd += f'tensor_converter ! '
    cmd += f'tensor_transform mode=arithmetic option=typecast:float32,add:-127.5,div:127.5 ! '

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
      library = find_nnapi_delegate_library()
      cmd += f'tensor_filter framework=tensorflow-lite throughput={self.THROUGHPUT} name=nn model={self.tflite_model} custom=Delegate:External,ExtDelegateLib:{library} ! '

    cmd += f'tensor_decoder mode=bounding_boxes option1=mobilenet-ssd option2={self.label_path} option3={self.box_priors} option4={self.VIDEO_WIDTH}:{self.VIDEO_HEIGHT} option5={self.MODEL_INPUT_WIDTH}:{self.MODEL_INPUT_HEIGHT} ! '
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
      self.loop = GLib.MainLoop()

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
  example.THROUGHPUT = args.throughput
  example.CAM_ROT = args.rot
  example.cam_type = args.cam_type

  if example.cam_type == 'uvc':
    example.VIDEO_WIDTH = 640
    example.VIDEO_HEIGHT = 480
  else:
    example.VIDEO_WIDTH = 1920
    example.VIDEO_HEIGHT = 1080

  example.VIDEO_WIDTH = args.width
  example.VIDEO_HEIGHT = args.height
 
  enable_performance(args.performance)

  example.build_pipeline(args.engine)
  example.run()
