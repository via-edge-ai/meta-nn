Onnxruntime
===========
Introduction
------------
ONNX Runtime is an open-source scoring engine for Open Neural Network Exchange (ONNX) models by Microsoft. Currently, the latest supported version is Onnxruntime 1.8.1.
Adding Onnxruntime to the yocto environment allows us to leverage the ".onnx" models and the graph optimizations by onnxruntime  whose popularity has grown considerably over the past few years.

About Onnxruntime package
-------------------------
The onnxruntime is installed by default on the ``rity-demo-image``.

The onnxruntime packages are broken down into three parts:

    * ``onnxruntime-staticdev``: add all onnxruntime static library files to your lib folder.
    * ``onnxruntime-examples`` : add the efficientnet-lite4 model to your bin folder along with two executables to run it. It would also add a folder called onnxruntime-example to your home directory containing a python script to test onnxruntime.
    * ``onnxruntime`` :  add all python packages required for onnxruntime.

Using Onnxruntime
-----------------
To test onnxruntime, follow the steps below:

.. prompt:: bash #

    cd /usr/bin/onnxruntime/examples/unitest
    ./onnx_test_runner efficientnet-lite4/ #this executable checks if all test cases are passed while running the model.
    ./onnxruntime_perf_test -t 10 efficientnet-lite4/efficientnet-lite4.onnx #this executable prints out various runtime metrics such as inference time, latency and more.


.. prompt:: bash #

    cd ~/onnxruntime_example/
    python3 onnxruntime_test.py #this script runs the kitten.jfif image through the efficientnet-lite4 onnx model and prints the top 5 predictions.
