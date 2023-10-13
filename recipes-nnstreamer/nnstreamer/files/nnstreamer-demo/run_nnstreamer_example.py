#!/usr/bin/env python

import os
import sys
import logging
from nnstreamer_example import *

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  args = argument_parser_init()
 
  tmp_args=''
  
  for i in sys.argv[1:]:
    tmp_args+=' '
    tmp_args+=i
  
  print(tmp_args)
  if args.app == 'image_classification':
    os.system("python3 nnstreamer_example_image_classification.py {0}".format(tmp_args))
  elif args.app == 'object_detection':
    os.system("python3 nnstreamer_example_object_detection.py {0}".format(tmp_args))
  elif args.app == 'object_detection_yolov5':
    os.system("python3 nnstreamer_example_object_detection_yolov5.py {0}".format(tmp_args))
  elif args.app == 'face_detection':
    os.system("python3 nnstreamer_example_face_detection.py {0}".format(tmp_args))
  elif args.app == 'pose_estimation':
    os.system("python3 nnstreamer_example_pose_estimation.py {0}".format(tmp_args))
  elif args.app == 'low_light_image_enhancement':
    os.system("python3 nnstreamer_example_low_light_image_enhancement.py {0}".format(tmp_args))

