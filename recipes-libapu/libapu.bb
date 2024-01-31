SUMMARY = "LibAPU host"
LICENSE = "MIT & Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE.md;md5=a8d8cf662ef6bf9936a1e1413585ecbf"

S = "${WORKDIR}/git"

DEPENDS = "libdrm"
RDEPENDS:${PN} = "libdrm-apu"

SRCREV = "01d91fa946522d56331522a8da2b97c90ba27d2e"
SRC_URI = "${AIOT_BSP_URI}/open-amp.git;branch=mtk-android-11;protocol=https"

EXTRA_OEMAKE = " \
    'PREFIX=${STAGING_DIR_TARGET}/usr/' \
"

do_compile() {
    oe_runmake -C apps/examples/apu/host/ libapu libxrp
}

do_install() {
    install -d ${D}${libdir}
    install -m 0555 ${S}/apps/examples/apu/host/libapu.a ${D}${libdir}/
    install -m 0555 ${S}/apps/examples/apu/host/libxrp.a ${D}${libdir}/

    install -d ${D}${includedir}
    install -d ${D}${includedir}/libapu
    install -m 0644 ${S}/apps/examples/apu/include/rich-iot/* ${D}${includedir}/libapu/
    install -m 0644 ${S}/apps/examples/apu/include/xrp/xrp_api.h ${D}${includedir}/libapu/
}

FILES:{PN}-staticdev = "${libdir}/*"
FILES:${PN} = "${includedir}"
