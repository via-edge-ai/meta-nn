DESCRIPTION = "Prebuilt libraries of Mediatek NeuroPilot"
LICENSE = "LicenseRef-MediaTek-AIoT-SLA-1"
LIC_FILES_CHKSUM = "file://LICENSE;md5=c25f59288708e3fd9961c9e6142aafee"

inherit features_check
REQUIRED_DISTRO_FEATURES = "nda-mtk"

DEPENDS += " libcxx ncurses "
RDEPENDS:${PN} += " libcxx ncurses libstdc++ python3-pillow "

PROVIDES = " \
	virtual/libneuron \
	virtual/ncc-tflite \
"

RPROVIDES:${PN} = " \
	libneuron \
	ncc-tflite \
"

BRANCH = "${DISTRO_CODENAME}"

SRCREV = "f929d5176893d1d94cba2ebae3a5854710c2cf75"
SRC_URI += "git://git@gitlab.com/mediatek/aiot/nda/mtk-neuropilot-prebuilts.git;protocol=ssh;branch=${BRANCH} \
"

S = "${WORKDIR}/git"

# Universal Neuron SDK (NP6 and later) needs hw settings. Handle hw settings installation for specific platforms.
HW_SETTINGS_REQUIRE = "${@bb.utils.contains_any('SOC_FAMILY', 'mt8188', '1', '0', d)}"

do_configure[noexec] = "1"
do_buildclean[noexec] = "1"

EXTRA_OEMAKE = ' \
	HW_SETTINGS_INSTALL=${HW_SETTINGS_REQUIRE} \
'

do_install() {
	if [ ${HW_SETTINGS_REQUIRE} = 1 ]; then
		bbplain "${SOC_FAMILY} requires hw settings"
		install -d ${D}/${sysconfdir}
		chown -R root:root ${D}/${sysconfdir}
		oe_runmake install PWD=${S}/${SOC_FAMILY} LIBDIR=${D}${libdir} INCLUDEDIR=${D}${includedir} DATADIR=${D}${datadir} SBINDIR=${D}${sbindir} ETCDIR=${D}${sysconfdir}
	else
		oe_runmake install PWD=${S}/${SOC_FAMILY} LIBDIR=${D}${libdir} INCLUDEDIR=${D}${includedir} DATADIR=${D}${datadir} SBINDIR=${D}${sbindir}
	fi

	chown -R root:root ${D}${libdir}/
}

FILES:${PN} += " \
	${datadir} ${libdir}/*.so \
	${@bb.utils.contains('HW_SETTINGS_REQUIRE', '1', '${sysconfdir}/*', '', d)} \
"

FILES_SOLIBSDEV = ""

INHIBIT_SYSROOT_STRIP = "1"
INHIBIT_PACKAGE_DEBUG_SPLIT = "1"
INHIBIT_PACKAGE_STRIP = "1"
INSANE_SKIP:${PN} += "already-stripped dev-so"
