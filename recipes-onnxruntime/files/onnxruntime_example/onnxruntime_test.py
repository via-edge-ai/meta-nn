# This script is developed with ideas from two sources:
# 1) https://github.com/onnx/tensorflow-onnx/blob/master/tutorials/efficientnet-lite.ipynb
# 2) https://github.com/tensorflow/tensorflow/blob/master/tensorflow/examples/label_image/label_image.py


import numpy as np
import math
import onnxruntime as rt
import cv2
import argparse
import time

with open('labels_map.txt', 'r') as f:
    labels = [l.rstrip() for l in f]

def img_stats(a, name={}):
    return {
        "name": name,
        "size": a.shape,
        "mean": "{:.2f}".format(a.mean()),
        "std": "{:.2f}".format(a.std()),
        "max": a.max(),
        "min": a.min(),
        "median": "{:.2f}".format(np.median(a)),
    }


def center_crop(img, out_height, out_width):
    height, width, _ = img.shape
    left = int((width - out_width) / 2)
    right = int((width + out_width) / 2)
    top = int((height - out_height) / 2)
    bottom = int((height + out_height) / 2)
    img = img[top:bottom, left:right]
    return img


def resize_with_aspectratio(img, out_height, out_width, scale=87.5, inter_pol=cv2.INTER_LINEAR):
    height, width, _ = img.shape
    new_height = int(100. * out_height / scale)
    new_width = int(100. * out_width / scale)
    if height > width:
        w = new_width
        h = int(new_height * height / width)
    else:
        h = new_height
        w = int(new_width * width / height)
    img = cv2.resize(img, (w, h), interpolation=inter_pol)
    return img


def pre_process(img, dims):
    output_height, output_width, _ = dims
    img = resize_with_aspectratio(img, output_height, output_width, inter_pol=cv2.INTER_LINEAR)
    img = center_crop(img, output_height, output_width)
    img = np.asarray(img, dtype='float32')
    img -= [127.0, 127.0, 127.0]
    img /= [128.0, 128.0, 128.0]
    return img


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", "-i", default='kitten.jfif', help="path of image to be processed")
    parser.add_argument("--labels","-l", default='labels_map.txt', help="path to file containing labels")
    parser.add_argument("--model", "-m", default='/usr/bin/onnxruntime/examples/unitest/efficientnet-lite4/efficientnet-lite4.onnx', help="Effecientnet-lite4 model path")
    args = parser.parse_args()


img = cv2.imread(args.image)
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# pre-process the image like mobilenet and resize it to 300x300
img = pre_process(img, (224, 224, 3))

# create a batch of 1 (that batch size is buned into the saved_model)
img_batch = np.expand_dims(img, axis=0)

# load the model
sess = rt.InferenceSession(args.model)
input_name = sess.get_inputs()[0].name


# run inference and print results


start_time = time.time()
results = sess.run(["Softmax:0"], {"images:0": img_batch})[0]
stop_time = time.time()

result = reversed(results[0].argsort()[-5:])
for r in result:
    print(results[0][r], labels[r])

print('time: {:.3f}ms'.format((stop_time - start_time) * 1000))
