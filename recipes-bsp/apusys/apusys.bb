DESCRIPTION = "Mediatek APUSYS Out-of-tree kernel driver"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=16de935ebcebe2420535844d4f6faefc"

COMPATIBLE_MACHINE = "mt8395"

inherit module

SRCREV = "9a3f0abe50a0b97d756d47c9e3d20f3c2d9934b5"

BRANCH = "${SOC_FAMILY}"

SRC_URI += "git://gitlab.com/mediatek/aiot/bsp/mtk-apusys-driver.git;protocol=https;branch=${BRANCH} \
"

S = "${WORKDIR}/git"

# The inherit of module.bbclass will automatically name module packages with
# "kernel-module-" prefix as required by the oe-core build environment.

RPROVIDES_${PN} += "kernel-module-apusys"
