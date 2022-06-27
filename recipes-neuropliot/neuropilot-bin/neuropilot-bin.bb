DESCRIPTION = "Prebuilt libraries of Mediatek NeuroPilot"
LICENSE = "LicenseRef-MediaTek-AIoT-SLA-1"
LIC_FILES_CHKSUM = "file://LICENSE;md5=c25f59288708e3fd9961c9e6142aafee"

inherit features_check
REQUIRED_DISTRO_FEATURES = "nda-mtk"
COMPATIBLE_MACHINE = "i1200-demo"

DEPENDS += " libcxx ncurses "
RDEPENDS:${PN} += " libcxx ncurses libstdc++ python3-pillow "
RPROVIDES:${PN} = " libapu_mdw libedma libmdla_ut libvpu5 libneuron "

SRCREV = "91fc66ec85096ed77bff4abacca0177db9bd3ff6"
BRANCH = "${DISTRO_CODENAME}"

SRC_URI += "git://git@gitlab.com/mediatek/aiot/nda/mtk-neuropilot-prebuilts.git;protocol=ssh;branch=${BRANCH} \
           "

S = "${WORKDIR}/git"

do_configure[noexec] = "1"
do_buildclean[noexec] = "1"

do_install() {
	oe_runmake install PWD=${S}/${SOC_FAMILY} LIBDIR=${D}${libdir} INCLUDEDIR=${D}${includedir} DATADIR=${D}${datadir} SBINDIR=${D}${sbindir}
	chown -R root:root ${D}${libdir}/
}

FILES:${PN} += " ${datadir} ${libdir}/*.so "

FILES_SOLIBSDEV = ""

INHIBIT_SYSROOT_STRIP = "1"
INHIBIT_PACKAGE_DEBUG_SPLIT = "1"
INHIBIT_PACKAGE_STRIP = "1"
INSANE_SKIP:${PN} += "already-stripped dev-so"
