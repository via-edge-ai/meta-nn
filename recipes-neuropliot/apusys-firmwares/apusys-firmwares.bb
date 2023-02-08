DESCRIPTION = "Prebuilt firmwares of Mediatek APUSYS"
LICENSE = "LicenseRef-MediaTek-AIoT-SLA-1"
LIC_FILES_CHKSUM = "file://LICENSE;md5=c25f59288708e3fd9961c9e6142aafee"

inherit features_check
REQUIRED_DISTRO_FEATURES = "nda-mtk"

SRCREV:mt8195 = "4384097490d9b277e9c7f7bbf3b84286dd8519a1"
SRCREV:mt8188 = "9c08e0beaf59d216a2c1d8314fee12202a189641"
BRANCH = "${SOC_FAMILY}"

SRC_URI += "git://git@gitlab.com/mediatek/aiot/nda/mtk-apusys-firmware.git;protocol=ssh;branch=${BRANCH} \
           "

S = "${WORKDIR}/git"

APUSYS_FIRMWARE = "apusys.sig.img"

do_install() {
	install -d ${D}/${nonarch_base_libdir}
	install -d ${D}/${nonarch_base_libdir}/firmware
	install -m 0644 ${S}/${APUSYS_FIRMWARE} ${D}/${nonarch_base_libdir}/firmware

	install -d ${D}/${sysconfdir}
	install -m 0644 ${S}/nhw ${D}/${sysconfdir}/nhw

	install -m 0644 ${S}/cam_vpu1.img ${D}/${nonarch_base_libdir}/firmware
	install -m 0644 ${S}/cam_vpu2.img ${D}/${nonarch_base_libdir}/firmware
	install -m 0644 ${S}/cam_vpu3.img ${D}/${nonarch_base_libdir}/firmware
}

FILES:${PN} += "\
	${nonarch_base_libdir}/firmware/* \
	${sysconfdir}/*\
"

INSANE_SKIP:${PN} += " arch already-stripped "
