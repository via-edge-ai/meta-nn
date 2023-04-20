FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

# Patches for building nnstreamer with tensorflow-lite, armnn and neuronsdk support
# on IoT Yocto.
SRC_URI:append = " \
	file://0001-nnstreamer-Fix-include-header-header-in-tensorflow-d.patch \
	file://0002-nnstreamer-Disable-nnapi.patch \
	file://0003-nnstreamer-Add-tensor-filter-neuronsdk.patch \
	file://0004-nnstreamer-Fix-unittest-fail.patch \
	file://0005-nnstreamer-example-Add-unit-test-fo-tensor-filter-ne.patch \
	file://sample_1x4x4x4_two_input_one_output.tflite \
	file://sample_1x4x4x4_two_input_two_output.tflite \
"

# Flags to check if neuron is available on current platform
NEURON_PLATFORM = "${@bb.utils.contains_any('SOC_FAMILY',  'mt8195 mt8188', '1', '0', d)}"
NEURON = "${@ "1" if d.getVar('NEURON_PLATFORM') == '1' and d.getVar('NDA_BUILD') == '1' else "0" }"

DEPENDS:append = "\
	python3-numpy-native \
	armnn \
	${@bb.utils.contains('NEURON', '1', 'virtual/libneuron', ' ', d)} \
	${@bb.utils.contains('TFLITE_PREBUILT', '1', 'tensorflowlite-prebuilt', 'tensorflow-lite', d)} \
"

# The original nnstreamer recipe does not have a fixed SRCREV,
# we fix SRCREV of nnstreamer for porting it on IoT Yocto.
SRCREV = "1d45516414fa46078e72007fe6295e50e1a6d0fc"


EXTRA_OEMESON:append = "\
	-Darmnn-support=enabled \
	-Dtflite2-support=enabled \
	-Dpython3-support=enabled \
	${@bb.utils.contains('NEURON', '1', '-Dneuronsdk-support=enabled', ' ', d)} \
	--buildtype=release \
"

do_install:append() {
	ln --relative --symbolic ${D}${libdir}/nnstreamer_python3.so ${D}${libdir}/nnstreamer_python.so

	install -m 644 ${WORKDIR}/sample_1x4x4x4_two_input_one_output.tflite ${D}${bindir}/unittest-nnstreamer/tests/test_models/models
	install -m 644 ${WORKDIR}/sample_1x4x4x4_two_input_two_output.tflite ${D}${bindir}/unittest-nnstreamer/tests/test_models/models
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