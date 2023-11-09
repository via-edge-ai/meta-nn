DESCRIPTION = "Prebuilt firmwares of Mediatek APUSYS"
LICENSE = "LicenseRef-MediaTek-AIoT-SLA-1"
LIC_FILES_CHKSUM = "file://LICENSE;md5=c25f59288708e3fd9961c9e6142aafee"

SRCREV:mt8195 = "2502c4bf3eabec12ef1d4a8098f419b2f1a2f6e0"
SRCREV:mt8188 = "9c08e0beaf59d216a2c1d8314fee12202a189641"
SRCREV:mt8370 = "9c08e0beaf59d216a2c1d8314fee12202a189641"
FIRMWARE_DIR:mt8195 = "mt8395"
FIRMWARE_DIR:mt8188 = "mt8390"
FIRMWARE_DIR:mt8370 = "mt8370"
BRANCH = "${SOC_FAMILY}"
# The firmware for mt8188 also supports mt8370
BRANCH:mt8370 = "mt8188"

SRC_URI += "git://git@gitlab.com/mediatek/aiot/bsp/mtk-apusys-firmware.git;protocol=ssh;branch=${BRANCH} \
           "

S = "${WORKDIR}/git"

APUSYS_FIRMWARE = "apusys.sig.img"

do_install() {
	install -d ${D}/${nonarch_base_libdir}
	install -d ${D}/${nonarch_base_libdir}/firmware
	install -d ${D}/${nonarch_base_libdir}/firmware/mediatek/
	install -d ${D}/${nonarch_base_libdir}/firmware/mediatek/${FIRMWARE_DIR}
	install -m 0644 ${S}/${APUSYS_FIRMWARE} ${D}/${nonarch_base_libdir}/firmware/mediatek/${FIRMWARE_DIR}

	install -d ${D}/${sysconfdir}
	install -m 0644 ${S}/nhw ${D}/${sysconfdir}/nhw
	install -m 0644 ${S}/cam_vpu1.img ${D}/${nonarch_base_libdir}/firmware/mediatek/${FIRMWARE_DIR}
	install -m 0644 ${S}/cam_vpu2.img ${D}/${nonarch_base_libdir}/firmware/mediatek/${FIRMWARE_DIR}
	install -m 0644 ${S}/cam_vpu3.img ${D}/${nonarch_base_libdir}/firmware/mediatek/${FIRMWARE_DIR}
}

FILES:${PN} += "\
	${nonarch_base_libdir}/firmware/* \
	${sysconfdir}/*\
"

INSANE_SKIP:${PN} += " arch already-stripped "
