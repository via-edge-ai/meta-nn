NNAPI
=====
Supported platforms
-------------------
NNAPI is supported only on ``i350`` and ``i500`` soc family.

Introduction
------------
Google has ported NNAPI from Android to their ChromeOS (`NNAPI on ChromeOS <https://chromium.googlesource.com/aosp/platform/frameworks/ml/+/refs/heads/master/nn/>`_). We basically adapted their work on yocto.

Currently NNAPI on Linux, supports only one HAL that needs to be built at compile time. We support three HALs : :ref:`nnapi:Cpu HAL`, :ref:`nnapi:ArmNN HAL` and :ref:`nnapi:Xtensa HAL (VP6)`.

A HAL is a dynamically shared library named ``libvendor-nn-hal.so``.

Available HAL
^^^^^^^^^^^^^
Cpu HAL
~~~~~~~
This is a very basic HAL that declares to handle only a very limited set of operations and does them on the CPU. No acceleration. This is used mainly for integration testing.

ArmNN HAL
~~~~~~~~~
This is the HAL to use the ArmNN framework that can leverage the GPU and Neon acceleration.

Xtensa HAL (VP6)
~~~~~~~~~~~~~~~~
This is the HAL to use the VP6 APU from Cadence.

.. note::
    A licence agreement with Cadence is needed in order to use the Xtensa HAL.

Building and adding the package
-------------------------------
If building an image for a supported platform, NNAPI will by default be included in the image. To ensure it is included, please ensure that the package ``packagegroup-rity-nnapi`` is installed.

The HAL to be compiled is specified using a virtual provider. You can specify it like this:

  * ``nnapi-cpu-hal`` (Cpu HAL) - default one
  * ``android-nn-driver`` (ArmNN HAL)
  * ``xtensa-ann-bin`` (Xtensa HAL)

Inside the ``build/conf/local.conf`` file:

.. code::

   PREFERRED_PROVIDER_virtual/libvendor-nn-hal = "android-nn-driver"

Using NNAPI
-----------
NNAPI is used as a tensorflow-lite delegate. To use it, please refer to the :doc:`tensorflow-lite` page.
