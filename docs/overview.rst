Overview
========

About meta-nn
-------------
``meta-nn`` is a collection of recipes to ease the integration of ai/ml frameworks over our rity sdk.

Supported frameworks
--------------------
.. csv-table:: Supported frameworks
        :header: "Frameworks", "Version", "Supported platforms"

        "Tensorflow-lite", 2.9.0, "all"
        "ARMNN", 22.02, "all"
        "NNAPI", 1.3, "i350, i500"
	"Onnxruntime", 1.8, "all"

Building AI/ML image
--------------------
The default ``rity-demo-image`` image contains all the supported ai/ml frameworks. Please refer to the `RITY SDK manual <https://mediatek.gitlab.io/aiot/rity/meta-rity/index.html>`_ to build and flash it.
