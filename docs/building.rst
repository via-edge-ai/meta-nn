Building AI/ML image
====================

.. note::
   This section assumes you are able to build and flash the RITY SDK as explained in the `RITY SDK manual <https://mediatek.gitlab.io/aiot/rity/meta-rity/index.html>`_. This guide will only describe commands that need to be adapted to build the AI/ML image compared to the default image.

Fetching the code
-----------------
To correctly fetch the code for AI/ML, you need to add ``-m rity-nn.xml`` on your repo init command such as:

.. parsed-literal::

   $ mkdir rity; cd rity
   $ repo init -u git@gitlab.com:mediatek/aiot/bsp/manifest.git -b |release| -m rity-nn.xml
   $ repo sync
   $ export TEMPLATECONF=${PWD}/src/meta-nn/conf/
   $ source src/poky/oe-init-build-env

Configuring the image
---------------------
local.conf
^^^^^^^^^^
Supported machines
~~~~~~~~~~~~~~~~~~
Please refer to the `BSP documentation <https://mediatek.gitlab.io/aiot/rity/meta-mediatek-bsp/boards/index.html>`_

Adding packages to the image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``meta-nn`` provides 2 packages that you can build and install : ``tensorflow-lite`` and ``armnn``, You can install the one you want using the following :

.. code::

   IMAGE_INSTALL_append = " tensorflow-lite "
   IMAGE_INSTALL_append = " armnn "

Building and flashing the image
-------------------------------
The image is built with the following command (just as the default rity image) :

.. prompt:: bash $

   bitbake rity-demo-image

To flash it, follow instructions in the `RITY SDK manual flashing section <https://mediatek.gitlab.io/aiot/rity/meta-rity/getting-started/flashing.html>`_
