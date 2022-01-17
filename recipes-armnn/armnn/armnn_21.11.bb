SUMMARY = "ARM Neural Network SDK"
DESCRIPTION = "Linux software and tools to enable machine learning Tensorflow lite workloads on power-efficient devices"
LICENSE = "MIT & Apache-2.0"
# Apache-2.0 license applies to mobilenet tarball
LIC_FILES_CHKSUM = "file://LICENSE;md5=3e14a924c16f7d828b8335a59da64074 \
                    file://${COMMON_LICENSE_DIR}/Apache-2.0;md5=89aea4e17d99a7cacdbeed46a0096b10"
inherit cmake

PV_MAJOR = "${@d.getVar('PV',d,1).split('.')[0]}"
PV_MINOR = "${@d.getVar('PV',d,1).split('.')[1]}"

SRCREV = "v${PV}"
BRANCH_ARMNN = "branches/armnn_${PV_MAJOR}_${PV_MINOR}"

SRC_URI = "git://github.com/ARM-software/armnn.git;branch=${BRANCH_ARMNN} \
           file://0001-fix-bd-compilation-issue.patch \
           file://0001-search-for-system-opencl-header.patch \
           "

S = "${WORKDIR}/git"

DEPENDS += " \
    flatbuffers-native \
    arm-compute-library \
    opencl-headers \
    opencl-headers-cxx \
    tensorflow-lite \
"
TARGET_CFLAGS += " -Wno-uninitialized "

RDEPENDS:${PN} = " arm-compute-library "

TESTVECS_INSTALL_DIR = "${datadir}/arm/armnn"


EXTRA_OECMAKE += " \
    -DARMCOMPUTECL=1 \
    -DARMCOMPUTENEON=1 \
    -DBUILD_UNIT_TESTS=0 \
    -DBUILD_ARMNN_SERIALIZER=1 \
    -DARMNNREF=1 \
    -DBUILD_ARMNN_TFLITE_DELEGATE=1 \
    -DTENSORFLOW_ROOT=${STAGING_INCDIR} \
    -DTfLite_Schema_INCLUDE_PATH=${STAGING_INCDIR}/tensorflow/lite/schema \
"

EXTRA_OEMAKE += "'LIBS=${LIBS}' 'CXX=${CXX}' 'CC=${CC}' 'AR=${AR}' 'CXXFLAGS=${CXXFLAGS}' 'CFLAGS=${CFLAGS}'"

do_install:append() {
    install -d ${D}${includedir}/armnnUtils
    install -m 0555 ${S}/src/armnnUtils/*.hpp ${D}${includedir}/armnnUtils

    install -d ${D}${includedir}/ghc
    install -m 0555 ${S}/third-party/ghc/*.hpp ${D}${includedir}/ghc

    install -d ${D}${includedir}/cxxopts
    install -m 0555 ${S}/third-party/cxxopts/*.hpp ${D}${includedir}/cxxopts

}

FILES:${PN} += "${TESTVECS_INSTALL_DIR} /usr/share/armnn/*"

FILES:${PN}-dev += "${libdir}/cmake/* ${libdir}/*.cmake"
INSANE_SKIP:${PN}-dev = "dev-elf"
