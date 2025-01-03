FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

# Patches for building nnstreamer with tensorflow-lite, armnn and neuronsdk support
# on IoT Yocto.
SRC_URI:append = " \
       file://0001-nnstreamer-Fix-include-header-header-in-tensorflow-d.patch \
       file://0002-nnstreamer-Disable-nnapi.patch \
       file://0003-nnstreamer-Add-tensor-filter-neuronsdk.patch \
       file://0004-nnstreamer-Fix-unittest-fail.patch \
       file://0005-nnstreamer-example-Add-unit-test-fo-tensor-filter-ne.patch \
       file://0006-nnstreamer-Fix-detect-objects-array-is-out-of-bound-.patch \
       file://0007-nnstreamer-Add-custom-property-debug-to-print-infere.patch \
       file://sample_1x4x4x4_two_input_one_output.tflite \
       file://sample_1x4x4x4_two_input_two_output.tflite \
       file://nnstreamer-demo \
       file://0008-nnstreamer-Update-neuron-delegate-version-to-6.3.3.patch \
       file://0001-nnstreamer-Add-Support-for-TFLite-stable-delegate.patch \
"

# Flags to check if neuron is available on current platform
NEURON_PLATFORM = "${@bb.utils.contains_any('SOC_FAMILY',  'mt8195 mt8188 mt8370', '1', '0', d)}"

DEPENDS:append = "\
	python3-numpy-native \
	armnn \
	${@bb.utils.contains('NEURON_PLATFORM', '1', 'virtual/libneuron', ' ', d)} \
	${@bb.utils.contains('TFLITE_PREBUILT', '1', 'tensorflowlite-prebuilt', 'tensorflow-lite', d)} \
"

# The original nnstreamer recipe does not have a fixed SRCREV,
# we fix SRCREV of nnstreamer for porting it on IoT Yocto.
SRCREV = "1d45516414fa46078e72007fe6295e50e1a6d0fc"


EXTRA_OEMESON:append = "\
	-Darmnn-support=enabled \
	-Dtflite2-support=enabled \
	-Dpython3-support=enabled \
	${@bb.utils.contains('NEURON_PLATFORM', '1', '-Dneuronsdk-support=enabled', ' ', d)} \
	--buildtype=release \
"

do_install:append() {
	ln --relative --symbolic ${D}${libdir}/nnstreamer_python3.so ${D}${libdir}/nnstreamer_python.so

	install -m 644 ${WORKDIR}/sample_1x4x4x4_two_input_one_output.tflite ${D}${bindir}/unittest-nnstreamer/tests/test_models/models
	install -m 644 ${WORKDIR}/sample_1x4x4x4_two_input_two_output.tflite ${D}${bindir}/unittest-nnstreamer/tests/test_models/models

	install -d ${D}${bindir}/nnstreamer-demo

	install -m 644 ${WORKDIR}/nnstreamer-demo/run_nnstreamer_example.py ${D}${bindir}/nnstreamer-demo
        install -m 644 ${WORKDIR}/nnstreamer-demo/nnstreamer_example.py ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/nnstreamer_example_pose_estimation.py ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/nnstreamer_example_object_detection_yolov5.py ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/nnstreamer_example_object_detection.py ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/nnstreamer_example_image_classification.py ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/nnstreamer_example_face_detection.py ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/nnstreamer_example_low_light_image_enhancement.py ${D}${bindir}/nnstreamer-demo
        install -m 644 ${WORKDIR}/nnstreamer-demo/nnstreamer_example_monocular_depth_estimation.py ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/yolov5s-int8.tflite ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/ssd_mobilenet_v2_coco.tflite ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/mobilenet_v1_1.0_224_quant.tflite ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/detect_face.tflite ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/lite-model_zero-dce_1.tflite ${D}${bindir}/nnstreamer-demo
        install -m 644 ${WORKDIR}/nnstreamer-demo/midas.tflite ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/box_priors.txt ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/coco.txt ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/coco_labels_list.txt ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/labels.txt ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/labels_face.txt ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/point_labels.txt ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/mosaic.png ${D}${bindir}/nnstreamer-demo
	install -m 644 ${WORKDIR}/nnstreamer-demo/original.png ${D}${bindir}/nnstreamer-demo
        
}

# The original nnstreamer recipe makes separate packages for tensorflow and unit test,
# but on IoT Yocto, we will install them by default.
# So we remove packages of tensorflow and unit test.
PACKAGES:remove = "\
	${PN}-unittest \
	${PN}-tensorflow-lite \
"

RDEPENDS:${PN}:append = "\
	${@bb.utils.contains('TFLITE_PREBUILT', '1', 'tensorflowlite-prebuilt', 'tensorflow-lite', d)} \
	gstreamer1.0-plugins-good \
	ssat \
"
