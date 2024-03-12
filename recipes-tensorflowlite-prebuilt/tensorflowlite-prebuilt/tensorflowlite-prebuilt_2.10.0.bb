DESCRIPTION = "Prebuilt libraries of TensorflowLite"
LICENSE = "BSD-3-Clause & Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE;md5=01bb7fe1aa5c0508107d2d7a87af3a9a"

inherit features_check
REQUIRED_DISTRO_FEATURES = "tflite-prebuilt"

DEPENDS += " libcxx ncurses "
RDEPENDS:${PN} += " \
    libcxx \
    ncurses \
    libstdc++ \
    python3 \
    python3-core \
    python3-numpy \
    python3-pillow \
"

SRCREV = "bdf2128a2cb37803e81894fc94ddbffcc3275e51"
BRANCH = "v2_10_0"
TFLITE_ENABLE_XNNPACK = "0"

SRC_URI += "${AIOT_RITY_URI}/tensorflowlite-prebuilt.git;protocol=https;branch=${BRANCH} \
           "

S = "${WORKDIR}/git"

do_configure[noexec] = "1"
do_buildclean[noexec] = "1"

do_install() {
	oe_runmake install PWD=${S} LIBDIR=${D}${libdir} INCLUDEDIR=${D}${includedir} DATADIR=${D}${datadir} SBINDIR=${D}${sbindir} TFLITE_XNNPACK=${TFLITE_ENABLE_XNNPACK}
	chown -R root:root ${D}${libdir}/
}

FILES:${PN} += " \
	${datadir} \
	${libdir} \
	${libdir}/pkgconfig/*.pc  \
"

FILES_SOLIBSDEV = ""

INHIBIT_SYSROOT_STRIP = "1"
INHIBIT_PACKAGE_DEBUG_SPLIT = "1"
INHIBIT_PACKAGE_STRIP = "1"
INSANE_SKIP:${PN} += "already-stripped dev-so"
