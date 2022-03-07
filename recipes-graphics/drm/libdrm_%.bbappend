FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += " \
        file://0001-Add-support-of-APU.patch \
        file://0002-Add-a-function-to-check-the-state-of-the-APU.patch \
        file://0003-Add-support-of-user-pointer.patch \
        file://0004-apu-Fix-the-logic-off-apu_device_online.patch \
       "

PACKAGECONFIG = "apu install-test-programs"
PACKAGECONFIG[apu] = "-Dapu=true"

PACKAGES =+ "${PN}-apu"
RRECOMMENDS:${PN}-drivers = "${PN}-apu"

FILES:${PN}-apu = "${libdir}/libdrm_apu.so.*"
