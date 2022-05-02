Tensorflow-lite
===============

About tflite
------------
We use tensorflow-lite as the enference engine for machine learning. Tensorflow-lite will delegate the computation on the available hardware through the use of delegates. We support several delegates:

    * gpu delegate
    * armnn delegate
    * nnapi delegate (on supported platforms, see :doc:`nnapi`)

Tflite models
-------------
The image installs one tensorflow-lite model that can be used with the :ref:`tensorflow-lite:Python image recognition demo` or :ref:`tensorflow-lite:benchmark_model tool`

    * ``/usr/share/label_image/mobilenet_v1_1.0_224_quant.tflite`` : quantized model

Python image recognition demo
-----------------------------
The image installs a python demo application for image recognition inside the ``/usr/share/label_image`` directory.

It is the upstream `label_image.py <https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/examples/python/label_image.py>`_, modified according to explanations available `here <https://www.tensorflow.org/lite/guide/python>`_.

To run the demo, run the following commands

.. prompt:: bash #

    cd /usr/share/label_image
    python3 label_image.py --label_file labels_mobilenet_quant_v1_224.txt --image grace_hopper.jpg --model_file mobilenet_v1_1.0_224_quant.tflite                                                                    #to run on the cpu
    python3 label_image.py --label_file labels_mobilenet_quant_v1_224.txt --image grace_hopper.jpg --model_file mobilenet_v1_1.0_224_quant.tflite -e /usr/lib(64)/gpu_external_delegate.so                           #to run on the gpu
    python3 label_image.py --label_file labels_mobilenet_quant_v1_224.txt --image grace_hopper.jpg --model_file mobilenet_v1_1.0_224_quant.tflite -e /usr/lib(64)/libarmnnDelegate.so.25 -o "backends:GpuAcc,CpuAcc" #to run on the gpu, using armnn delegate
    python3 label_image.py --label_file labels_mobilenet_quant_v1_224.txt --image grace_hopper.jpg --model_file mobilenet_v1_1.0_224_quant.tflite -e /usr/lib(64)/nnapi_external_delegate.so                         #to run using nnapi delegate


The image should contain necessary packages to do python development such as the python tflite runtime and pip3.

benchmark_model tool
--------------------
We can also use ``benchmark_model`` to measure performances.

To run ``benchmark_model`` with gpu delegate, use the following command:

.. prompt:: bash #

    benchmark_model --graph=/usr/share/label_image/mobilenet_v1_1.0_224_quant.tflite --use_gpu=1

To run ``benchmark_model`` with the armnn delegate use the following command:

.. prompt:: bash #

   benchmark_model --external_delegate_path=/usr/lib(64)/libarmnnDelegate.so.25 --external_delegate_options="backends:GpuAcc,CpuAcc" --graph=/usr/share/label_image/mobilenet_v1_1.0_224_quant.tflite --num_runs=1

.. note::
   You should adapt the command depending on whether your system supports multilib or not i.e ``/usr/lib/libarmnnDelegate.so.25`` or ``/usr/lib64/libarmnnDelegate.so.25``


To run ``benchmark_model`` with the nnapi delegate use the following command:

.. prompt:: bash #

   benchmark_model --graph=/usr/share/label_image/mobilenet_v1_1.0_224_quant.tflite --use_nnapi=1 --num_runs=1

