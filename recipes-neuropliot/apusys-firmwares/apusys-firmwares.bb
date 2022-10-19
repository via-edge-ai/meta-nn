DESCRIPTION = "Prebuilt firmwares of Mediatek APUSYS"
LICENSE = "LicenseRef-MediaTek-AIoT-SLA-1"
LIC_FILES_CHKSUM = "file://LICENSE;md5=c25f59288708e3fd9961c9e6142aafee"

inherit features_check
REQUIRED_DISTRO_FEATURES = "nda-mtk"
COMPATIBLE_MACHINE = "(i1200-demo|genio-700-evk)"

SRCREV:mt8195 = "2c0cf45d10eecc538e39850c38a5250c63a42077"
SRCREV:mt8188 = "5b94a6b8dcb0063ade5ea5b6bf7bda37a23b3861"
BRANCH = "${SOC_FAMILY}"

SRC_URI += "git://git@gitlab.com/mediatek/aiot/nda/mtk-apusys-firmware.git;protocol=ssh;branch=${BRANCH} \
           "

S = "${WORKDIR}/git"

APUSYS_FIRMWARE:mt8195 = "mrv.elf"
APUSYS_FIRMWARE:mt8188 = "apusys.img"

do_install() {
	install -d ${D}/${nonarch_base_libdir}
	install -d ${D}/${nonarch_base_libdir}/firmware
	install -m 0644 ${S}/${APUSYS_FIRMWARE} ${D}/${nonarch_base_libdir}/firmware
	install -m 0644 ${S}/cam_vpu1.img ${D}/${nonarch_base_libdir}/firmware
	install -m 0644 ${S}/cam_vpu2.img ${D}/${nonarch_base_libdir}/firmware
	install -m 0644 ${S}/cam_vpu3.img ${D}/${nonarch_base_libdir}/firmware
}

FILES:${PN} += "${nonarch_base_libdir}/firmware/*"
INSANE_SKIP:${PN} += " arch already-stripped "