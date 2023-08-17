#!/usr/bin/env python

import os
import sys
import gi
import re
import logging
import argparse
import subprocess
import math
import numpy as np
import cairo

############################################################################
#
#  // Download model
#  mkdir -p nnstreamer-demo
#  cd nnstreamer-demo
#  download_url="http://ci.nnstreamer.ai/warehouse/nnmodels/"
#  wget ${download_url}/detect_face.tflite
#  wget ${download_url}/labels_face.txt
#  wget ${download_url}/box_priors.txt
#
#  // Push to device
#  adb push nnstreamer-demo /usr/bin/
#
############################################################################

gi.require_version('Gst', '1.0')
gi.require_version('GstGL', '1.0')

from gi.repository import Gst, GstGL, GObject
from nnstreamer_example import *

DEBUG = False

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

    self.BOX_SIZE = 4
    self.LABEL_SIZE = 2
    self.DETECTION_MAX = 1917
    self.MAX_OBJECT_DETECTION = 10

    self.Y_SCALE = 10.0
    self.X_SCALE = 10.0
    self.H_SCALE = 5.0
    self.W_SCALE = 5.0


    self.CAM_ID = 0

    self.tflite_model = ''
    self.dla = ''
    self.tflite_labels = []
    self.tflite_box_priors = []
    self.detected_objects = []
    self.pattern = None
    self.mask_pattern_path = ''

    self.filter = None
    self.invoke_ms = 0
    self.avgfps = 0

    if not self.tflite_init():
        raise Exception

    GObject.threads_init()
    Gst.init(argv)

  def build_pipeline(self, engine):
    cmd = ''
    cmd += f'v4l2src name=src device=/dev/video{self.CAM_ID} ! video/x-raw,width=2048,height=1536,format=YUY2,framerate=30/1 ! tee name=t_raw '
    cmd += f't_raw. ! queue leaky=2 max-size-buffers=10 ! '
    cmd += f'v4l2convert output-io-mode=dmabuf-import extra-controls="cid,rotate={self.CAM_ROT}" ! video/x-raw,width={self.VIDEO_WIDTH},height={self.VIDEO_HEIGHT},format=RGB16,pixel-aspect-ratio=1/1 ! '
    cmd += f'cairooverlay name=tensor_res ! '
    cmd += f'fpsdisplaysink name=sink text-overlay=false signal-fps-measurements=true sync=false video-sink="glimagesink sync=false qos=false " '

    cmd += f't_raw. ! queue leaky=2 max-size-buffers=2 ! '
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
      logging.error('Not support NNAPI')

    cmd += f'tensor_sink name=res_face '

    self.pipeline = Gst.parse_launch(cmd)
    logging.info("pipeline: %s" % cmd)

  def new_data_cb(self, sink, buffer):
      if self.running:
          if buffer.n_memory() != 2:
              return False
          #  face detection
          #  input[0] float32 [3:300:300:1] (RGB:SSD_MODEL_INPUT_WIDTH:SSD_MODEL_INPUT_HEIGHT:1)
          #  output[0] float32 [4:1:1917:1] (SSD_BOX_SIZE:1:SSD_DETECTION_MAX:1)
          #  output[1] float32 [2:1917:1:1] (LABEL_SIZE:SSD_DETECTION_MAX:1:1)

          # boxes
          mem_boxes = buffer.peek_memory(0)
          result1, info_boxes = mem_boxes.map(Gst.MapFlags.READ)
          if result1:
              decoded_boxes = list(np.frombuffer(info_boxes.data, dtype=np.float32))  # decode bytestrings to float list

          # detections
          mem_detections = buffer.peek_memory(1)
          result2, info_detections = mem_detections.map(Gst.MapFlags.READ)
          if result2:
              decoded_detections = list(np.frombuffer(info_detections.data, dtype=np.float32)) # decode bytestrings to float list

          idx = 0

          boxes = []
          for _ in range(self.DETECTION_MAX):
              box = []
              for _ in range(self.BOX_SIZE):
                  box.append(decoded_boxes[idx])
                  idx += 1
              boxes.append(box)

          idx = 0

          detections = []
          for _ in range(self.DETECTION_MAX):
              detection = []
              for _ in range(self.LABEL_SIZE):
                  detection.append(decoded_detections[idx])
                  idx += 1
              detections.append(detection)

          self.get_detected_objects(detections, boxes)

          mem_boxes.unmap(info_boxes)
          mem_detections.unmap(info_detections)

  def iou(self, A, B):
      x1 = max(A['x'], B['x'])
      y1 = max(A['y'], B['y'])
      x2 = min(A['x'] + A['width'], B['x'] + B['width'])
      y2 = min(A['y'] + A['height'], B['y'] + B['height'])
      w = max(0, (x2 - x1 + 1))
      h = max(0, (y2 - y1 + 1))
      inter = float(w * h)
      areaA = float(A['width'] * A['height'])
      areaB = float(B['width'] * B['height'])
      o = float(inter / (areaA + areaB - inter))
      return o if o >= 0 else 0

  def nms(self, detected):
      threshold_iou = 0.5
      detected = sorted(detected, key=lambda a: a['prob'])
      boxes_size = len(detected)

      _del = [False for _ in range(boxes_size)]

      for i in range(boxes_size):
          if not _del[i]:
              for j in range(i + 1, boxes_size):
                  if self.iou(detected[i], detected[j]) > threshold_iou:
                      _del[j] = True

      # update result
      self.detected_objects.clear()

      for i in range(boxes_size):
          if not _del[i]:
              self.detected_objects.append(detected[i])

              if DEBUG:
                  print("==============================")
                  print("LABEL           : {}".format(self.tflite_labels[detected[i]["class_id"]]))
                  print("x               : {}".format(detected[i]["x"]))
                  print("y               : {}".format(detected[i]["y"]))
                  print("width           : {}".format(detected[i]["width"]))
                  print("height          : {}".format(detected[i]["height"]))
                  print("Confidence Score: {}".format(detected[i]["prob"]))

  def get_detected_objects(self, detections, boxes):
      threshold_score = 0.5
      detected = list()

      for d in range(self.DETECTION_MAX):
          ycenter = boxes[d][0] / self.Y_SCALE * self.tflite_box_priors[2][d] + self.tflite_box_priors[0][d]
          xcenter = boxes[d][1] / self.X_SCALE * self.tflite_box_priors[3][d] + self.tflite_box_priors[1][d]
          h = math.exp(boxes[d][2] / self.H_SCALE) * self.tflite_box_priors[2][d]
          w = math.exp(boxes[d][3] / self.W_SCALE) * self.tflite_box_priors[3][d]

          ymin = ycenter - h / 2.0
          xmin = xcenter - w / 2.0
          ymax = ycenter + h / 2.0
          xmax = xcenter + w / 2.0

          x = xmin * self.MODEL_INPUT_WIDTH
          y = ymin * self.MODEL_INPUT_HEIGHT
          width = (xmax - xmin) * self.MODEL_INPUT_WIDTH
          height = (ymax - ymin) * self.MODEL_INPUT_HEIGHT

          for c in range(1, self.LABEL_SIZE):
              score = 1.0 / (1.0 + math.exp(-detections[d][c]))

              # This score cutoff is taken from Tensorflow's demo app.
              # There are quite a lot of nodes to be run to convert it to the useful possibility
              # scores. As a result of that, this cutoff will cause it to lose good detections in
              # some scenarios and generate too much noise in other scenario.

              if score < threshold_score:
                  continue

              obj = {
                  'class_id': c,
                  'x': x,
                  'y': y,
                  'width': width,
                  'height': height,
                  'prob': score
              }

              detected.append(obj)

      self.nms(detected)

  # @brief Store the information from the caps that we are interested in.
  def prepare_overlay_cb(self, overlay, caps):
      self.video_caps = caps

  # @brief Callback to draw the overlay.
  def draw_overlay_cb(self, overlay, context, timestamp, duration):
      if self.video_caps == None or not self.running:
          return

      # mutex_lock alternative required
      detected = self.detected_objects
      # mutex_unlock alternative needed

      drawed = 0
      calculated = 0

      face_sizes = [0 for _ in range(len(detected))]

      for idx, obj in enumerate(detected):
          width = obj['width'] * self.VIDEO_WIDTH // self.MODEL_INPUT_WIDTH
          height = obj['height'] * self.VIDEO_HEIGHT // self.MODEL_INPUT_HEIGHT
          face_sizes[idx] = width * height

          calculated += 1
          if calculated >= self.MAX_OBJECT_DETECTION:
              break

      if len(face_sizes) != 0:
          target_image_idx = face_sizes.index(max(face_sizes))

      for idx, obj in enumerate(detected):
          label = self.tflite_labels[obj['class_id']][:-1]
          x = obj['x'] * self.VIDEO_WIDTH // self.MODEL_INPUT_WIDTH
          y = obj['y'] * self.VIDEO_HEIGHT // self.MODEL_INPUT_HEIGHT
          width = obj['width'] * self.VIDEO_WIDTH // self.MODEL_INPUT_WIDTH
          height = obj['height'] * self.VIDEO_HEIGHT // self.MODEL_INPUT_HEIGHT

          # implement pixelated pattern
          #if not (len(face_sizes) <= 1 or idx == target_image_idx):
          context.rectangle(x, y, width, height)
          context.set_source(self.pattern)
          context.fill()

          drawed += 1
          if drawed >= self.MAX_OBJECT_DETECTION:
              break

      if self.THROUGHPUT == '1':
              text = f'Camera FPS: {self.avgfps:.2f}, Invoke Time(ms):{round(self.invoke_ms, 2)}'
              context.select_font_face('Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
              context.set_font_size(20.0)
              context.set_source_rgb(1, 1, 1)
              (x, y, w, h, dx, dy) = context.text_extents(text)
              context.move_to((self.VIDEO_WIDTH - w) / 2.0, (self.VIDEO_HEIGHT - h) / 10.0)
              context.show_text(text)
      return

  def set_mask_pattern(self):
      """
      Prepare mask pattern for cairooverlay.
      """
      source = cairo.ImageSurface.create_from_png(self.mask_pattern_path)
      self.pattern = cairo.SurfacePattern(source)
      self.pattern.set_extend(cairo.Extend.REPEAT)

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
      self.avgfps = avgfps

  def run(self):
      logging.info("Run: Face detection.")

      # main loop
      self.loop = GObject.MainLoop()

      # set mask pattern (for mosaic pattern)
      self.set_mask_pattern()

      # bus and message callback
      bus = self.pipeline.get_bus()
      bus.add_signal_watch()
      bus.connect('message', self.on_bus_message)

      # tensor sink signal : new data callback
      tensor_sink = self.pipeline.get_by_name('res_face')
      tensor_sink.connect('new-data', self.new_data_cb)

      tensor_res = self.pipeline.get_by_name('tensor_res')
      tensor_res.connect('draw', self.draw_overlay_cb)
      tensor_res.connect('caps-changed', self.prepare_overlay_cb)

      if self.THROUGHPUT == '1':
          self.filter = self.pipeline.get_by_name("nn")
          # tensor_filter src signal : buffer ready callback
          srcpad = self.filter.get_static_pad("src")
          srcpad.add_probe(Gst.PadProbeType.BUFFER, self.on_buffer)

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
      tflite_model = 'detect_face.tflite'
      dla = 'detect_face.dla'
      tflite_label = 'labels_face.txt'
      tflite_box_prior = 'box_priors.txt'
      mask_pattern = 'mosaic.png'

      current_folder = os.path.dirname(os.path.abspath(__file__))
      model_folder = os.path.join(current_folder, '')

      self.tflite_model = os.path.join(model_folder, tflite_model)
      self.dla = os.path.join(model_folder, dla)
      if not os.path.exists(self.tflite_model):
          logging.error('cannot find tflite model [%s]', self.tflite_model)
          return False

      label_path = os.path.join(model_folder, tflite_label)
      try:
          with open(label_path, 'r') as label_file:
              for line in label_file.readlines():
                  self.tflite_labels.append(line)
      except FileNotFoundError:
          logging.error('cannot find tflite label [%s]', label_path)
          return False

      box_prior_path = os.path.join(model_folder, tflite_box_prior)
      try:
          with open(box_prior_path, 'r') as box_prior_file:
              for line in box_prior_file.readlines():
                  datas = list(map(float, line.split()))
                  self.tflite_box_priors.append(datas)
      except FileNotFoundError:
          logging.error('cannot find tflite label [%s]', box_prior_path)
          return False

      self.mask_pattern_path = os.path.join(model_folder, mask_pattern)
      if not os.path.exists(self.mask_pattern_path):
          logging.error('cannot find mask texture [%s]', self.mask_pattern_path)
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

  performance_hint(args.performance)

  example.build_pipeline(args.engine)
  example.run()
