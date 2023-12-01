DESCRIPTION = "Prebuilt libraries of Mediatek NeuroPilot"
LICENSE = "LicenseRef-MediaTek-AIoT-SLA-1"
LIC_FILES_CHKSUM = "file://LICENSE;md5=c25f59288708e3fd9961c9e6142aafee"

DEPENDS += " libcxx ncurses "
RDEPENDS:${PN} += " libcxx ncurses libstdc++ python3-pillow python3-numpy zlib "

PROVIDES = " \
	virtual/libneuron \
	virtual/ncc-tflite \
"

RPROVIDES:${PN} = " \
	libneuron \
	ncc-tflite \
"

BRANCH = "${DISTRO_CODENAME}"

SRCREV = "ad82387a034eb191251a3eddb955840e46d959e9"
SRC_URI += "git://git@gitlab.com/mediatek/aiot/rity/mtk-neuropilot-prebuilts.git;protocol=ssh;branch=${BRANCH} \
"

S = "${WORKDIR}/git"

NP_VERSION = "6"
MDW_VERSION="android13"

do_configure[noexec] = "1"
do_buildclean[noexec] = "1"

do_install() {
	oe_runmake install PWD=${S} LIBDIR=${D}${libdir} INCLUDEDIR=${D}${includedir} DATADIR=${D}${datadir} SBINDIR=${D}${sbindir} NP_VER=${NP_VERSION} MDW_VER=${MDW_VERSION}

	chown -R root:root ${D}${libdir}/
}

FILES:${PN} += " \
	${datadir} ${libdir}/*.so \
"

FILES_SOLIBSDEV = ""

INHIBIT_SYSROOT_STRIP = "1"
INHIBIT_PACKAGE_DEBUG_SPLIT = "1"
INHIBIT_PACKAGE_STRIP = "1"
INSANE_SKIP:${PN} += "already-stripped dev-so"
