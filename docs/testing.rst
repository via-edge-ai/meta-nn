Testing and using AI/ML tools
=============================

Tensorflow-lite
---------------
About tflite models
^^^^^^^^^^^^^^^^^^^
The image installs two tensorflow-lite models that can be used with the :ref:`testing:Python image recognition demo` or :ref:`testing:benchmark_model tool`

    * ``/home/root/label_image/mobilenet_v2_1.0_224_quant.tflite`` : quantized model
    * ``/home/root/label_image/mobilenet_v2_1.0_224.tflite`` : float model

Python image recognition demo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The image installs a python demo application for image recognition inside the ``/home/root/label_image`` directory.

It is directly adapted from the upstream `label_image.py <https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/examples/python/label_image.py>`_ and modified according to explanations available `here <https://www.tensorflow.org/lite/guide/python>`_.

We also added two flags: ``--use_gpu`` and ``--use_armnn`` to allow using gpu and armnn delegates. To run gpu/armnn delegate we use the experimental `load_delegate API <https://www.tensorflow.org/api_docs/python/tf/lite/experimental/load_delegate>`_.

To run the demo, run the following commands

.. prompt:: bash #

    cd label_image
    python3 label_image.py --label_file labels.txt --image grace_hopper.jpg --model_file mobilenet_v2_1.0_224_quant.tflite             #to run on the cpu
    python3 label_image.py --label_file labels.txt --image grace_hopper.jpg --model_file mobilenet_v2_1.0_224_quant.tflite --use_gpu   #to run on the gpu
    python3 label_image.py --label_file labels.txt --image grace_hopper.jpg --model_file mobilenet_v2_1.0_224_quant.tflite --use_armnn #to run on the gpu, using armnn delegate


The image should contain necessary packages to do python development such as the python tflite runtime and pip3.

benchmark_model tool
^^^^^^^^^^^^^^^^^^^^
We can also use ``benchmark_model`` to measure performances.

To run ``benchmark_model`` with gpu delegate, and the float model use the following command:

.. prompt:: bash #

    benchmark_model --graph=/home/root/label_image/mobilenet_v2_1.0_224.tflite --use_gpu=1

To run ``benchmark_model`` with the armnn delegate, and the float model use the following command:

.. prompt:: bash #

   benchmark_model --external_delegate_path=/usr/lib(64)/libarmnnDelegate.so.24 --external_delegate_options="backends:GpuAcc,CpuAcc" --graph=/home/root/label_image/mobilenet_v2_1.0_224.tflite --num_runs=1

.. note::
   You should adapt the command depending on whether your system supports multilib or not i.e ``/usr/lib/libarmnnDelegate.so.24`` or ``/usr/lib64/libarmnnDelegate.so.24``
