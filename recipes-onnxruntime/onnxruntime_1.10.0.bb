DESCRIPTION = "ONNX Runtime is an open-source scoring engine for Open Neural \
Network Exchange (ONNX) models. ONNX Runtime has an open architecture that \
is continually evolving to address the newest developments and challenges \
in AI and Deep Learning."
SUMMARY = "ONNX Runtime"
HOMEPAGE = "https://github.com/microsoft/onnxruntime"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://../LICENSE;md5=0f7e3b1308cb5c00b372a6e78835732d"

PACKAGES += "${PN}-examples ${PN}-examples-dbg"

SRCREV_FORMAT = "onnxruntime"

SRCREV_onnxruntime ="0d9030e79888d1d5828730b254fedc53c7b640c1"

S = "${WORKDIR}/git/cmake"

inherit python3native cmake

SRC_URI = " \
	gitsm://github.com/microsoft/onnxruntime.git;protocol=https;branch=rel-${PV};name=onnxruntime \
	file://efficientnet-lite4/test_data_set_0/input_0.pb \
	file://efficientnet-lite4/test_data_set_0/output_0.pb \
	file://efficientnet-lite4/test_data_set_1/input_0.pb \
	file://efficientnet-lite4/test_data_set_1/output_0.pb \
	file://efficientnet-lite4/test_data_set_2/input_0.pb \
	file://efficientnet-lite4/test_data_set_2/output_0.pb \
	file://efficientnet-lite4/efficientnet-lite4.onnx \
	file://onnxruntime_example/onnxruntime_test.py \
	file://onnxruntime_example/labels_map.txt \
	file://onnxruntime_example/kitten.jfif \
"

do_configure:prepend() {
	cd ${WORKDIR}/git/cmake/external/protobuf
	# Onnxruntime 1.10.0 by default uses protobuf v3.17.3,
	#however, honister provides v3.18.0. Hence checking out this branch for consistency.
	git checkout tags/v3.19.4
	cd ${WORKDIR}/build
}



DEPENDS += " \
	cmake-native \
	protobuf-native \
	zlib \
	python3 \
	python3-numpy \
	python3-numpy-native \
"

EXTRA_OECMAKE=" \
	-DCMAKE_BUILD_TYPE=Release \
	-DONNX_CUSTOM_PROTOC_EXECUTABLE=${STAGING_DIR_NATIVE}${prefix}/bin/protoc \
	-DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=ONLY \
	-DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER \
	-DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=ONLY \
	-DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=ONLY \
	-DCMAKE_SYSTEM_PROCESSOR=arm64 \
	-Dprotobuf_WITH_ZLIB=OFF \
	-Donnxruntime_GCC_STATIC_CPP_RUNTIME=ON \
	-DCMAKE_FIND_ROOT_PATH=${STAGING_DIR_TARGET} \
	-Donnxruntime_BUILD_SHARED_LIB=OFF \
	-Donnxruntime_DEV_MODE=OFF \
	-Donnxruntime_ENABLE_PYTHON=ON \
"

# Workaround for network access issue during compile step
# this needs to be fixed in the recipes buildsystem to move
# this such that it can be accomplished during do_fetch task
do_compile[network] = "1"

do_install() {
	install -d ${D}${libdir}

	cp --parents \
		$(find . -name "*.a") \
		${D}/${libdir}

	install -d ${D}${bindir}/${PN}-${PV}/examples

	install -d ${D}${bindir}/${PN}-${PV}/examples/unitest

	install -m 0555 \
		${WORKDIR}/build/onnx_test_runner \
		${D}${bindir}/${PN}-${PV}/examples/unitest

	install -m 0555 \
		${WORKDIR}/build/onnxruntime_perf_test \
		${D}${bindir}/${PN}-${PV}/examples/unitest

	cp -r \
		${WORKDIR}/efficientnet-lite4 \
		${D}${bindir}/${PN}-${PV}/examples/unitest

	install -d ${D}/home/root/onnxruntime_example

	install -m 644 ${WORKDIR}/onnxruntime_example/labels_map.txt ${D}/home/root/onnxruntime_example

	install -m 644 ${WORKDIR}/onnxruntime_example/kitten.jfif ${D}/home/root/onnxruntime_example

	install -m 644 ${WORKDIR}/onnxruntime_example/onnxruntime_test.py ${D}/home/root/onnxruntime_example


	install -d ${D}${libdir}/${PYTHON_DIR}/site-packages

	cp -r \
		${WORKDIR}/build/onnxruntime/ \
		${D}${libdir}/${PYTHON_DIR}/site-packages

	cd ${D}${bindir}
	ln -sf ${PN}-${PV} ${PN}
}

ALLOW_EMPTY:${PN} = "1"

FILES:${PN} = ""

FILES:${PN}-staticdev = " \
	${libdir} \
"

FILES:${PN}-examples = " \
	${bindir}/${PN} \
	${bindir}/${PN}-${PV}/examples/unitest \
	${bindir}/${PN}-${PV}/examples/unitest/efficientnet-lite4 \
	/home/root/onnxruntime_example \
"

FILES:${PN}-examples-dbg = " \
	${bindir}/${PN}-${PV}/examples/unitest/.debug \
	${bindir}/${PN}-${PV}/examples/inference/.debug \
"

FILES:python3-${PN} = " \
	${libdir}/${PYTHON_DIR} \
	${libdir}/${PYTHON_DIR}/site-packages \
	${libdir}/${PYTHON_DIR}/site-packages/onnxruntime \
"
