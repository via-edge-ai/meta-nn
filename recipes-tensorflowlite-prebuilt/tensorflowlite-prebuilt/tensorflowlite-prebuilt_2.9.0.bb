DESCRIPTION = "Prebuilt libraries of TensorflowLite"
LICENSE = "LicenseRef-MediaTek-AIoT-SLA-1"
LIC_FILES_CHKSUM = "file://LICENSE;md5=8c0955bebf11ce7b765fb08bf037af92"

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

SRCREV = "5992d2808148426f5932e9e56db9fed9e050d72b"

SRC_URI += "${AIOT_RITY_URI}/tensorflowlite-prebuilt.git;protocol=ssh;branch=main \
           "

S = "${WORKDIR}/git"

do_configure[noexec] = "1"
do_buildclean[noexec] = "1"

do_install() {
	oe_runmake install PWD=${S} LIBDIR=${D}${libdir} INCLUDEDIR=${D}${includedir} DATADIR=${D}${datadir} SBINDIR=${D}${sbindir}
	chown -R root:root ${D}${libdir}/
}

FILES:${PN} += " ${datadir} ${libdir} "

FILES_SOLIBSDEV = ""

INHIBIT_SYSROOT_STRIP = "1"
INHIBIT_PACKAGE_DEBUG_SPLIT = "1"
INHIBIT_PACKAGE_STRIP = "1"
INSANE_SKIP:${PN} += "already-stripped dev-so"
